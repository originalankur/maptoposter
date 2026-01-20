"""
Advanced Sound Map Generator
Adds water sounds, park ambience, and elevation-based pitch shifting
"""

import osmnx as ox
import networkx as nx
from midiutil import MIDIFile
import random
import math
import argparse
import os
from datetime import datetime
from geopy.geocoders import Nominatim
import time

SOUND_MAPS_DIR = "sound_maps"

class AdvancedCityMusician:
    """
    Enhanced version with water features, parks, and elevation mapping.
    """
    
    def __init__(self, G, water_features=None, parks=None, mode='random_walk', tempo=120, 
                 use_elevation=False):
        self.G = G
        self.water = water_features
        self.parks = parks
        self.mode = mode
        self.tempo = tempo
        self.use_elevation = use_elevation
        
        # 16 tracks for richer compositions
        self.midi = MIDIFile(16)
        
        # Extended track assignments
        self.tracks = {
            'motorway': 0,
            'primary': 1,
            'secondary': 2,
            'tertiary': 3,
            'residential': 4,
            'water_flow': 5,      # Rivers, streams
            'water_ambient': 6,   # Lakes, ponds
            'park_birds': 7,      # Park bird sounds
            'park_wind': 8,       # Wind through trees
            'intersection': 9,    # Percussion
            'harmony': 10,        # Chord progressions
            'bass_drone': 11,     # Sustained bass
            'melody': 12,         # Main melodic line
            'atmosphere': 13,     # Ambient textures
            'rhythm': 14,         # Rhythmic elements
            'special_fx': 15      # Special effects
        }
        
        # Instruments (General MIDI)
        self.instruments = {
            'motorway': 33,          # Acoustic Bass
            'primary': 0,            # Acoustic Grand Piano
            'secondary': 4,          # Electric Piano
            'tertiary': 48,          # String Ensemble
            'residential': 24,       # Acoustic Guitar
            'water_flow': 79,        # Ocarina (flowing sound)
            'water_ambient': 88,     # Pad 1 (new age)
            'park_birds': 123,       # Bird Tweet
            'park_wind': 92,         # Pad 5 (bowed)
            'intersection': 115,     # Woodblock
            'harmony': 19,           # Church Organ
            'bass_drone': 89,        # Pad 2 (warm)
            'melody': 73,            # Flute
            'atmosphere': 95,        # Pad 8 (sweep)
            'rhythm': 118,           # Synth Drum
            'special_fx': 98         # FX 3 (crystal)
        }
        
        # Initialize all tracks
        for track_name, track_num in self.tracks.items():
            self.midi.addTempo(track_num, 0, tempo)
            if track_name in self.instruments:
                self.midi.addProgramChange(track_num, 0, 0, self.instruments[track_name])
        
        self.current_time = 0
        self.note_count = defaultdict(int)
        
        # Musical scales for different moods
        self.scales = {
            'major': [0, 2, 4, 5, 7, 9, 11],      # Happy, bright
            'minor': [0, 2, 3, 5, 7, 8, 10],      # Melancholic
            'pentatonic': [0, 2, 4, 7, 9],        # Asian influence
            'blues': [0, 3, 5, 6, 7, 10],         # Bluesy
            'dorian': [0, 2, 3, 5, 7, 9, 10],     # Jazz, medieval
        }
        
        self.current_scale = self.scales['pentatonic']  # Default
    
    def set_scale(self, scale_name):
        """Change the musical scale/mode."""
        if scale_name in self.scales:
            self.current_scale = self.scales[scale_name]
    
    def quantize_to_scale(self, pitch, root=60):
        """
        Snap a pitch to the current musical scale.
        Makes everything sound more harmonious.
        """
        # Get octave and note
        octave = (pitch // 12) * 12
        note = pitch % 12
        
        # Find closest note in scale
        scale_notes = [(root % 12 + interval) % 12 for interval in self.current_scale]
        closest = min(scale_notes, key=lambda x: abs(x - note))
        
        return octave + closest
    
    def road_type_to_pitch(self, highway_type, quantize=True):
        """Enhanced pitch mapping with scale quantization."""
        pitch_ranges = {
            'motorway': (36, 43),        # C2 to G2
            'primary': (48, 55),         # C3 to G3
            'secondary': (55, 62),       # G3 to D4
            'tertiary': (60, 67),        # C4 to G4
            'residential': (67, 74),     # G4 to D5
        }
        
        track_name = self.road_type_to_track(highway_type)
        if track_name in pitch_ranges:
            low, high = pitch_ranges[track_name]
            pitch = random.randint(low, high)
        else:
            pitch = random.randint(60, 72)
        
        if quantize:
            pitch = self.quantize_to_scale(pitch)
        
        return pitch
    
    def road_type_to_track(self, highway_type):
        """Map highway type to track."""
        if highway_type in ['motorway', 'motorway_link', 'trunk', 'trunk_link']:
            return 'motorway'
        elif highway_type in ['primary', 'primary_link']:
            return 'primary'
        elif highway_type in ['secondary', 'secondary_link']:
            return 'secondary'
        elif highway_type in ['tertiary', 'tertiary_link']:
            return 'tertiary'
        else:
            return 'residential'
    
    def add_note_from_edge(self, u, v, data):
        """Convert street segment to note with elevation awareness."""
        highway = data.get('highway', 'unclassified')
        
        if isinstance(highway, list):
            highway = highway[0] if highway else 'unclassified'
        
        track_name = self.road_type_to_track(highway)
        track_num = self.tracks[track_name]
        
        # Base pitch
        pitch = self.road_type_to_pitch(highway)
        
        # Elevation modulation (if available)
        if self.use_elevation:
            try:
                elevation_u = self.G.nodes[u].get('elevation', 0)
                elevation_v = self.G.nodes[v].get('elevation', 0)
                avg_elevation = (elevation_u + elevation_v) / 2
                
                # Higher elevation = higher pitch (shift up to 12 semitones)
                elevation_shift = int((avg_elevation / 100) % 12)
                pitch = min(127, pitch + elevation_shift)
            except:
                pass
        
        duration = min(max(data.get('length', 100) / 200, 0.25), 2.0)
        
        # Dynamic velocity based on road type
        velocity_map = {
            'motorway': (90, 110),
            'primary': (75, 95),
            'secondary': (60, 80),
            'tertiary': (50, 70),
            'residential': (40, 60)
        }
        vel_range = velocity_map.get(track_name, (50, 70))
        velocity = random.randint(*vel_range)
        
        self.midi.addNote(track_num, 0, pitch, self.current_time, duration, velocity)
        self.note_count[track_name] += 1
        self.current_time += duration
        
        return duration
    
    def add_water_ambience(self):
        """Add flowing water sounds based on water features."""
        if self.water is None or self.water.empty:
            return
        
        print("🌊 Adding water ambience...")
        
        # Add sustained pad for water presence
        track_num = self.tracks['water_ambient']
        
        # Long sustained notes
        for i in range(5):
            pitch = self.quantize_to_scale(random.choice([48, 52, 55, 60]))  # Low ambient tones
            start_time = i * 8  # Every 8 beats
            duration = 8
            velocity = 40  # Quiet, ambient
            
            self.midi.addNote(track_num, 0, pitch, start_time, duration, velocity)
        
        # Flowing water (faster notes)
        track_num = self.tracks['water_flow']
        water_time = 0
        
        for _ in range(20):  # 20 water droplet sounds
            pitch = self.quantize_to_scale(random.randint(72, 84))
            duration = random.choice([0.25, 0.5, 0.75])
            velocity = random.randint(30, 50)
            
            self.midi.addNote(track_num, 0, pitch, water_time, duration, velocity)
            water_time += random.uniform(0.5, 2.0)
    
    def add_park_soundscape(self):
        """Add natural sounds for parks/green spaces."""
        if self.parks is None or self.parks.empty:
            return
        
        print("🌳 Adding park soundscape...")
        
        # Bird chirps
        track_num = self.tracks['park_birds']
        park_time = 0
        
        for _ in range(15):  # 15 bird chirps
            pitch = random.randint(84, 96)  # High pitched
            duration = random.choice([0.125, 0.25])
            velocity = random.randint(40, 70)
            
            self.midi.addNote(track_num, 0, pitch, park_time, duration, velocity)
            park_time += random.uniform(1.0, 3.0)
        
        # Wind through trees (soft pads)
        track_num = self.tracks['park_wind']
        
        for i in range(3):
            pitch = self.quantize_to_scale(random.choice([55, 60, 64]))
            start_time = i * 10
            duration = 10
            velocity = 35
            
            self.midi.addNote(track_num, 0, pitch, start_time, duration, velocity)
    
    def add_bass_drone(self):
        """Add a sustained bass drone for atmosphere."""
        track_num = self.tracks['bass_drone']
        
        # Root note drone
        root = 36  # C2
        duration = min(self.current_time, 64)  # Up to 64 beats
        
        self.midi.addNote(track_num, 0, root, 0, duration, 60)
        print(f"🎸 Added bass drone (root: {root})")
    
    def add_harmonic_progression(self):
        """Add chord progression for harmonic richness."""
        track_num = self.tracks['harmony']
        
        # Simple I-IV-V-I progression in C
        chords = [
            [48, 52, 55],  # C major (I)
            [53, 57, 60],  # F major (IV)
            [55, 59, 62],  # G major (V)
            [48, 52, 55],  # C major (I)
        ]
        
        time_pos = 0
        chord_duration = 4  # 4 beats per chord
        
        # Repeat progression
        for _ in range(min(4, int(self.current_time / 16))):
            for chord in chords:
                for note in chord:
                    self.midi.addNote(track_num, 0, note, time_pos, chord_duration, 50)
                time_pos += chord_duration
        
        print(f"🎹 Added harmonic progression")
    
    def traverse_random_walk(self, duration=90):
        """Enhanced random walk with musical awareness."""
        print("🎵 Composing in RANDOM WALK mode...")
        
        current_node = random.choice(list(self.G.nodes()))
        target_beats = (duration / 60) * self.tempo
        
        while self.current_time < target_beats:
            neighbors = list(self.G.neighbors(current_node))
            
            if not neighbors:
                current_node = random.choice(list(self.G.nodes()))
                continue
            
            next_node = random.choice(neighbors)
            edge_data = self.G.get_edge_data(current_node, next_node)
            
            if edge_data:
                if isinstance(edge_data, dict) and 0 in edge_data:
                    edge_data = edge_data[0]
                
                self.add_note_from_edge(current_node, next_node, edge_data)
                
                # Add percussion at intersections
                if random.random() < 0.12:
                    degree = self.G.degree(next_node)
                    if degree >= 3:
                        pitch = 42 if degree >= 4 else 46
                        self.midi.addNote(self.tracks['intersection'], 9, pitch, 
                                        self.current_time, 0.25, 70)
            
            current_node = next_node
        
        # Add ambient layers
        self.add_water_ambience()
        self.add_park_soundscape()
        self.add_bass_drone()
        self.add_harmonic_progression()
        
        print(f"✓ Composition complete:")
        for track, count in self.note_count.items():
            if count > 0:
                print(f"   {track}: {count} notes")
    
    def compose(self):
        """Main composition orchestrator."""
        if self.mode == 'random_walk':
            self.traverse_random_walk(duration=120)  # 2 minute piece
        else:
            raise ValueError(f"Mode {self.mode} not implemented in advanced version")
    
    def save(self, filename):
        """Save MIDI file."""
        with open(filename, "wb") as output_file:
            self.midi.writeFile(output_file)
        print(f"✓ Saved: {filename}")


def get_coordinates(city, country):
    """Geocode city to coordinates."""
    print("📍 Looking up coordinates...")
    geolocator = Nominatim(user_agent="advanced_sound_map")
    time.sleep(1)
    
    location = geolocator.geocode(f"{city}, {country}")
    
    if location:
        print(f"✓ {location.address}")
        print(f"✓ {location.latitude}, {location.longitude}")
        return (location.latitude, location.longitude)
    else:
        raise ValueError(f"Could not find {city}, {country}")


def create_advanced_sound_map(city, country, point, dist, scale, tempo, output_file):
    """Create advanced sound map with water and parks."""
    print(f"\n🎼 ADVANCED Sound Map: {city}, {country}")
    print(f"   Scale: {scale}")
    print(f"   Tempo: {tempo} BPM")
    print(f"   Radius: {dist}m\n")
    
    # Download street network
    print("📡 Downloading street network...")
    G = ox.graph_from_point(point, dist=dist, dist_type='bbox', network_type='all')
    print(f"✓ {len(G.nodes())} nodes, {len(G.edges())} edges")
    
    # Download water features
    print("📡 Downloading water features...")
    try:
        water = ox.features_from_point(point, tags={'natural': 'water', 'waterway': True}, dist=dist)
        print(f"✓ Found {len(water)} water features")
    except:
        water = None
        print("⚠ No water features found")
    
    # Download parks
    print("📡 Downloading parks...")
    try:
        parks = ox.features_from_point(point, tags={'leisure': 'park', 'landuse': 'grass'}, dist=dist)
        print(f"✓ Found {len(parks)} parks")
    except:
        parks = None
        print("⚠ No parks found")
    
    # Create musician
    musician = AdvancedCityMusician(G, water, parks, mode='random_walk', tempo=tempo)
    musician.set_scale(scale)
    
    # Compose
    musician.compose()
    
    # Save
    musician.save(output_file)
    
    duration = (musician.current_time / tempo) * 60
    print(f"\n✅ Complete! Duration: {duration:.1f}s ({duration/60:.1f} min)")


def generate_output_filename(city, scale, tempo):
    """Generate output filename."""
    if not os.path.exists(SOUND_MAPS_DIR):
        os.makedirs(SOUND_MAPS_DIR)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    city_slug = city.lower().replace(' ', '_')
    filename = f"{city_slug}_advanced_{scale}_tempo{tempo}_{timestamp}.mid"
    return os.path.join(SOUND_MAPS_DIR, filename)


if __name__ == "__main__":
    from collections import defaultdict
    
    parser = argparse.ArgumentParser(
        description="Advanced Sound Map Generator with water, parks, and harmonies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Pentatonic scale (Asian-influenced)
  python create_sound_map_advanced.py -c "Tokyo" -C "Japan" -s pentatonic -d 6000
  
  # Minor scale (melancholic)
  python create_sound_map_advanced.py -c "Venice" -C "Italy" -s minor -d 4000 -t 80
  
  # Major scale (bright, happy)
  python create_sound_map_advanced.py -c "Mumbai" -C "India" -s major -d 8000 -t 130
  
  # Blues scale (groovy)
  python create_sound_map_advanced.py -c "New Orleans" -C "USA" -s blues -d 5000 -t 110

Musical Scales:
  major       - Happy, bright (C D E F G A B)
  minor       - Sad, contemplative (C D Eb F G Ab Bb)
  pentatonic  - Asian, peaceful (C D E G A)
  blues       - Groovy, American (C Eb F F# G Bb)
  dorian      - Jazz, medieval (C D Eb F G A Bb)

Features:
  ✓ Multi-track orchestration (16 instruments)
  ✓ Water ambience (rivers, lakes)
  ✓ Park soundscapes (birds, wind)
  ✓ Bass drones
  ✓ Harmonic progressions
  ✓ Scale-quantized melodies
        """
    )
    
    parser.add_argument('--city', '-c', type=str, required=True)
    parser.add_argument('--country', '-C', type=str, required=True)
    parser.add_argument('--scale', '-s', type=str, default='pentatonic',
                       choices=['major', 'minor', 'pentatonic', 'blues', 'dorian'])
    parser.add_argument('--distance', '-d', type=int, default=5000)
    parser.add_argument('--tempo', '-t', type=int, default=100)
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🎵 ADVANCED SOUND MAP GENERATOR")
    print("=" * 70)
    
    try:
        coords = get_coordinates(args.city, args.country)
        output_file = generate_output_filename(args.city, args.scale, args.tempo)
        
        create_advanced_sound_map(
            args.city,
            args.country,
            coords,
            args.distance,
            args.scale,
            args.tempo,
            output_file
        )
        
        print("\n" + "=" * 70)
        print("🎧 Listen to your city's sound!")
        print("=" * 70)
        print(f"\nFile: {output_file}")
        print("\nPlay with:")
        print("  • https://signal.vercel.app/edit")
        print("  • MuseScore, GarageBand, FL Studio")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
