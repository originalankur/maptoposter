import osmnx as ox
import networkx as nx
from midiutil import MIDIFile
import random
import math
from collections import defaultdict
import argparse
import os
from datetime import datetime
from geopy.geocoders import Nominatim
import time

SOUND_MAPS_DIR = "sound_maps"

class CityMusician:
    """
    Converts street networks into music.
    Maps road features to musical parameters.
    """
    
    def __init__(self, G, mode='grid_scan', tempo=120):
        """
        Initialize the city musician.
        
        Args:
            G: OSMnx graph of street network
            mode: Traversal mode ('grid_scan', 'random_walk', 'shortest_path', 'depth_first')
            tempo: BPM (beats per minute)
        """
        self.G = G
        self.mode = mode
        self.tempo = tempo
        self.midi = MIDIFile(8)  # 8 tracks for different road types
        
        # Track assignments (instrument channels)
        self.tracks = {
            'motorway': 0,      # Bass
            'primary': 1,       # Piano
            'secondary': 2,     # Electric Piano
            'tertiary': 3,      # Strings
            'residential': 4,   # Acoustic Guitar
            'water': 5,         # Synth Pad
            'parks': 6,         # Flute
            'ambient': 7        # Percussion/FX
        }
        
        # MIDI instrument numbers (General MIDI standard)
        self.instruments = {
            'motorway': 33,      # Acoustic Bass
            'primary': 0,        # Acoustic Grand Piano
            'secondary': 4,      # Electric Piano 1
            'tertiary': 48,      # String Ensemble 1
            'residential': 24,   # Acoustic Guitar (nylon)
            'water': 88,         # Pad 1 (new age)
            'parks': 73,         # Flute
            'ambient': 115       # Woodblock (percussion)
        }
        
        # Initialize all tracks
        for road_type, track_num in self.tracks.items():
            self.midi.addTempo(track_num, 0, tempo)
            if road_type in self.instruments:
                self.midi.addProgramChange(track_num, 0, 0, self.instruments[road_type])
        
        self.current_time = 0  # Current time in beats
        
    def road_type_to_pitch(self, highway_type):
        """
        Maps road type to MIDI pitch (note).
        Higher importance roads = lower pitch (bass)
        """
        pitch_map = {
            'motorway': [36, 38, 40, 43],           # C2, D2, E2, G2 - Deep bass
            'motorway_link': [36, 38, 40],
            'trunk': [41, 43, 45],                  # F2, G2, A2
            'trunk_link': [41, 43, 45],
            'primary': [48, 50, 52, 55],            # C3, D3, E3, G3 - Mid bass
            'primary_link': [48, 50, 52],
            'secondary': [55, 57, 59, 60],          # G3, A3, B3, C4 - Mid range
            'secondary_link': [55, 57, 59],
            'tertiary': [60, 62, 64, 67],           # C4, D4, E4, G4 - Higher
            'tertiary_link': [60, 62, 64],
            'residential': [67, 69, 71, 72],        # G4, A4, B4, C5 - Melody range
            'living_street': [67, 69, 71],
            'unclassified': [64, 67, 69],           # E4, G4, A4
        }
        
        # Get pitch options for this road type
        pitches = pitch_map.get(highway_type, [60, 64, 67])  # Default: C major chord
        return random.choice(pitches)
    
    def road_type_to_track(self, highway_type):
        """Determine which track/instrument to use for this road type."""
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
    
    def length_to_duration(self, length):
        """
        Convert street length (meters) to note duration (beats).
        Longer streets = longer notes
        """
        # Normalize: 100m street = 0.5 beats, 500m street = 1 beat
        duration = min(max(length / 200, 0.25), 2.0)  # Clamp between 0.25 and 2 beats
        return duration
    
    def add_note_from_edge(self, u, v, data):
        """
        Convert a single street segment (edge) into a musical note.
        """
        highway = data.get('highway', 'unclassified')
        
        # Handle list of highway types
        if isinstance(highway, list):
            highway = highway[0] if highway else 'unclassified'
        
        # Get musical parameters
        track_name = self.road_type_to_track(highway)
        track_num = self.tracks[track_name]
        pitch = self.road_type_to_pitch(highway)
        duration = self.length_to_duration(data.get('length', 100))
        
        # Velocity (volume): major roads louder
        if 'motorway' in highway or 'trunk' in highway:
            velocity = random.randint(90, 110)
        elif 'primary' in highway:
            velocity = random.randint(75, 95)
        elif 'secondary' in highway:
            velocity = random.randint(60, 80)
        else:
            velocity = random.randint(50, 70)
        
        # Add the note to MIDI
        self.midi.addNote(
            track_num,
            0,  # channel
            pitch,
            self.current_time,
            duration,
            velocity
        )
        
        # Advance time
        self.current_time += duration
        
        return duration
    
    def add_intersection_percussion(self, node):
        """
        Add percussion hit at intersections.
        More connections = louder hit
        """
        degree = self.G.degree(node)
        
        if degree >= 4:  # Major intersection
            pitch = 42  # Closed Hi-Hat
            velocity = 80
        elif degree == 3:  # T-intersection
            pitch = 46  # Open Hi-Hat
            velocity = 60
        else:  # Simple connection
            return  # Skip
        
        track_num = self.tracks['ambient']
        self.midi.addNote(track_num, 9, pitch, self.current_time, 0.25, velocity)  # Channel 9 = percussion
    
    def traverse_grid_scan(self):
        """
        Traverse the network in a grid-like pattern.
        Like reading a book: left to right, top to bottom.
        """
        print("🎵 Composing in GRID SCAN mode...")
        
        # Get all nodes with their positions
        nodes_with_pos = []
        for node in self.G.nodes():
            if 'y' in self.G.nodes[node] and 'x' in self.G.nodes[node]:
                y = self.G.nodes[node]['y']
                x = self.G.nodes[node]['x']
                nodes_with_pos.append((node, y, x))
        
        # Sort: top to bottom, then left to right
        nodes_with_pos.sort(key=lambda n: (-n[1], n[2]))
        
        visited_edges = set()
        
        for node, _, _ in nodes_with_pos:
            # Get all edges from this node
            for neighbor in self.G.neighbors(node):
                edge_key = tuple(sorted([node, neighbor]))
                
                if edge_key not in visited_edges:
                    visited_edges.add(edge_key)
                    
                    # Get edge data
                    edge_data = self.G.get_edge_data(node, neighbor)
                    if edge_data:
                        # Handle multi-edges (multiple roads between same nodes)
                        if isinstance(edge_data, dict) and 0 in edge_data:
                            edge_data = edge_data[0]
                        
                        self.add_note_from_edge(node, neighbor, edge_data)
                    
                    # Add percussion at intersections occasionally
                    if random.random() < 0.1:
                        self.add_intersection_percussion(node)
        
        print(f"✓ Generated {len(visited_edges)} notes from street network")
    
    def traverse_random_walk(self, duration=60):
        """
        Random walk through the network.
        Creates more organic, wandering soundscapes.
        
        Args:
            duration: Target duration in seconds
        """
        print("🎵 Composing in RANDOM WALK mode...")
        
        # Start at a random node
        current_node = random.choice(list(self.G.nodes()))
        target_beats = (duration / 60) * self.tempo  # Convert seconds to beats
        
        notes_added = 0
        
        while self.current_time < target_beats:
            # Get neighbors
            neighbors = list(self.G.neighbors(current_node))
            
            if not neighbors:
                # Dead end, jump to random node
                current_node = random.choice(list(self.G.nodes()))
                continue
            
            # Choose random neighbor (weighted by road importance)
            next_node = random.choice(neighbors)
            
            # Get edge data
            edge_data = self.G.get_edge_data(current_node, next_node)
            if edge_data:
                if isinstance(edge_data, dict) and 0 in edge_data:
                    edge_data = edge_data[0]
                
                self.add_note_from_edge(current_node, next_node, edge_data)
                notes_added += 1
                
                # Occasional percussion
                if random.random() < 0.15:
                    self.add_intersection_percussion(next_node)
            
            # Move to next node
            current_node = next_node
        
        print(f"✓ Generated {notes_added} notes from random walk")
    
    def traverse_depth_first(self):
        """
        Depth-first traversal of the network.
        Creates structured, exploratory compositions.
        """
        print("🎵 Composing in DEPTH-FIRST mode...")
        
        visited_edges = set()
        start_node = random.choice(list(self.G.nodes()))
        
        def dfs(node):
            for neighbor in self.G.neighbors(node):
                edge_key = tuple(sorted([node, neighbor]))
                
                if edge_key not in visited_edges:
                    visited_edges.add(edge_key)
                    
                    edge_data = self.G.get_edge_data(node, neighbor)
                    if edge_data:
                        if isinstance(edge_data, dict) and 0 in edge_data:
                            edge_data = edge_data[0]
                        
                        self.add_note_from_edge(node, neighbor, edge_data)
                        
                        if random.random() < 0.12:
                            self.add_intersection_percussion(neighbor)
                    
                    dfs(neighbor)
        
        dfs(start_node)
        print(f"✓ Generated {len(visited_edges)} notes from depth-first traversal")
    
    def compose(self):
        """
        Main composition method - orchestrates the music generation.
        """
        if self.mode == 'grid_scan':
            self.traverse_grid_scan()
        elif self.mode == 'random_walk':
            self.traverse_random_walk(duration=90)  # 90 second piece
        elif self.mode == 'depth_first':
            self.traverse_depth_first()
        else:
            raise ValueError(f"Unknown mode: {self.mode}")
    
    def save(self, filename):
        """Save the composed music to a MIDI file."""
        with open(filename, "wb") as output_file:
            self.midi.writeFile(output_file)
        print(f"✓ Saved MIDI file: {filename}")


def get_coordinates(city, country):
    """Fetch coordinates for a city."""
    print("Looking up coordinates...")
    geolocator = Nominatim(user_agent="sound_map_generator")
    time.sleep(1)
    
    location = geolocator.geocode(f"{city}, {country}")
    
    if location:
        print(f"✓ Found: {location.address}")
        print(f"✓ Coordinates: {location.latitude}, {location.longitude}")
        return (location.latitude, location.longitude)
    else:
        raise ValueError(f"Could not find coordinates for {city}, {country}")


def create_sound_map(city, country, point, dist, mode, tempo, output_file):
    """
    Main function to create a sound map.
    """
    print(f"\n🎼 Generating sound map for {city}, {country}...")
    print(f"   Mode: {mode}")
    print(f"   Tempo: {tempo} BPM")
    print(f"   Radius: {dist}m\n")
    
    # Download street network
    print("📡 Downloading street network data...")
    G = ox.graph_from_point(point, dist=dist, dist_type='bbox', network_type='all')
    print(f"✓ Downloaded {len(G.nodes())} intersections, {len(G.edges())} streets")
    
    # Create musician and compose
    musician = CityMusician(G, mode=mode, tempo=tempo)
    musician.compose()
    
    # Save MIDI
    musician.save(output_file)
    
    # Calculate duration
    duration_seconds = (musician.current_time / tempo) * 60
    print(f"\n🎵 Composition complete!")
    print(f"   Duration: {duration_seconds:.1f} seconds ({duration_seconds/60:.1f} minutes)")
    print(f"   Total beats: {musician.current_time:.1f}")


def generate_output_filename(city, mode, tempo):
    """Generate output filename."""
    if not os.path.exists(SOUND_MAPS_DIR):
        os.makedirs(SOUND_MAPS_DIR)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    city_slug = city.lower().replace(' ', '_')
    filename = f"{city_slug}_{mode}_tempo{tempo}_{timestamp}.mid"
    return os.path.join(SOUND_MAPS_DIR, filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate music from city street networks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Grid scan - systematic traversal
  python create_sound_map.py -c "Venice" -C "Italy" -m grid_scan -d 3000
  
  # Random walk - organic wandering
  python create_sound_map.py -c "Tokyo" -C "Japan" -m random_walk -d 5000 -t 140
  
  # Depth-first - structured exploration
  python create_sound_map.py -c "Paris" -C "France" -m depth_first -d 4000 -t 90
  
  # Your hometown
  python create_sound_map.py -c "Mumbai" -C "India" -m random_walk -d 6000

Modes:
  grid_scan    - Systematic left-to-right, top-to-bottom (structured)
  random_walk  - Random wandering through streets (organic, ambient)
  depth_first  - Deep exploration of paths (exploratory)

The generated MIDI files can be opened in:
  - GarageBand (Mac)
  - FL Studio, Ableton Live (Windows/Mac)
  - MuseScore (Free, cross-platform)
  - Online MIDI players
        """
    )
    
    parser.add_argument('--city', '-c', type=str, required=True, help='City name')
    parser.add_argument('--country', '-C', type=str, required=True, help='Country name')
    parser.add_argument('--mode', '-m', type=str, default='random_walk',
                       choices=['grid_scan', 'random_walk', 'depth_first'],
                       help='Traversal mode (default: random_walk)')
    parser.add_argument('--distance', '-d', type=int, default=5000,
                       help='Map radius in meters (default: 5000)')
    parser.add_argument('--tempo', '-t', type=int, default=120,
                       help='Tempo in BPM (default: 120)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎵 SOUND MAP GENERATOR")
    print("=" * 60)
    
    try:
        # Get coordinates
        coords = get_coordinates(args.city, args.country)
        
        # Generate output filename
        output_file = generate_output_filename(args.city, args.mode, args.tempo)
        
        # Create sound map
        create_sound_map(
            args.city, 
            args.country, 
            coords, 
            args.distance, 
            args.mode, 
            args.tempo, 
            output_file
        )
        
        print("\n" + "=" * 60)
        print("✅ Sound map generation complete!")
        print("=" * 60)
        print(f"\n🎧 Open your MIDI file in any music software:")
        print(f"   {output_file}")
        print("\nRecommended players:")
        print("   • Online: https://signal.vercel.app/edit (paste MIDI)")
        print("   • Desktop: MuseScore, GarageBand, FL Studio")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
