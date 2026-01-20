# 🎵 Sound Map Generator

Transform city street networks into music! This project converts the geometry and characteristics of urban landscapes into MIDI compositions.

## 🎼 What It Does

- **Downloads** real street network data from OpenStreetMap
- **Maps** different road types to different instruments and pitches
- **Generates** MIDI files you can play in any music software
- **Creates** unique musical signatures for each city

## 🚀 Installation

### Step 1: Install Dependencies

```bash
# Install the MIDI library
pip install -r requirements_sound.txt

# Or manually:
pip install MIDIUtil
```

You should already have these from the main poster project:
- osmnx
- networkx
- geopy

### Step 2: Test It!

```bash
# Basic version - simple and fast
python create_sound_map.py -c "Venice" -C "Italy" -d 3000

# Advanced version - with water sounds and harmonies
python create_sound_map_advanced.py -c "Venice" -C "Italy" -d 3000 -s pentatonic
```

## 🎹 Two Versions Available

### 1. **Basic Version** (`create_sound_map.py`)
Simple, focused on street networks only.

**Features:**
- 3 traversal modes (grid scan, random walk, depth-first)
- Different instruments for different road types
- Fast generation
- Good for learning the concept

### 2. **Advanced Version** (`create_sound_map_advanced.py`)
Rich, layered compositions with environmental sounds.

**Features:**
- 16-track orchestration
- Water ambience (rivers, lakes)
- Park soundscapes (birds, wind)
- Bass drones and harmonic progressions
- Musical scale quantization
- More atmospheric and musical

## 🎮 Basic Version Usage

```bash
python create_sound_map.py [OPTIONS]
```

### Options:
- `-c, --city` - City name (required)
- `-C, --country` - Country name (required)
- `-m, --mode` - Traversal mode (default: random_walk)
  - `grid_scan` - Systematic left-to-right, top-to-bottom
  - `random_walk` - Random wandering (most organic)
  - `depth_first` - Deep exploration of paths
- `-d, --distance` - Map radius in meters (default: 5000)
- `-t, --tempo` - BPM (default: 120)

### Examples:

```bash
# Random walk through Tokyo (organic, ambient)
python create_sound_map.py -c "Tokyo" -C "Japan" -m random_walk -d 6000 -t 140

# Grid scan of Manhattan (structured)
python create_sound_map.py -c "New York" -C "USA" -m grid_scan -d 5000 -t 110

# Depth-first exploration of Paris
python create_sound_map.py -c "Paris" -C "France" -m depth_first -d 4000 -t 90

# Your hometown
python create_sound_map.py -c "Mumbai" -C "India" -m random_walk -d 6000
```

## 🎨 Advanced Version Usage

```bash
python create_sound_map_advanced.py [OPTIONS]
```

### Options:
- `-c, --city` - City name (required)
- `-C, --country` - Country name (required)
- `-s, --scale` - Musical scale (default: pentatonic)
  - `major` - Happy, bright
  - `minor` - Melancholic, contemplative
  - `pentatonic` - Asian-influenced, peaceful
  - `blues` - Groovy, American
  - `dorian` - Jazz, medieval
- `-d, --distance` - Map radius in meters (default: 5000)
- `-t, --tempo` - BPM (default: 100)

### Examples:

```bash
# Pentatonic Tokyo (peaceful, Asian-influenced)
python create_sound_map_advanced.py -c "Tokyo" -C "Japan" -s pentatonic -d 6000 -t 100

# Minor Venice (melancholic, with water sounds)
python create_sound_map_advanced.py -c "Venice" -C "Italy" -s minor -d 4000 -t 80

# Blues New Orleans (groovy!)
python create_sound_map_advanced.py -c "New Orleans" -C "USA" -s blues -d 5000 -t 110

# Major Mumbai (bright and energetic)
python create_sound_map_advanced.py -c "Mumbai" -C "India" -s major -d 8000 -t 130
```

## 🎧 How to Listen

MIDI files are saved in the `sound_maps/` directory.

### Online (Easiest):
1. Go to https://signal.vercel.app/edit
2. Upload your .mid file
3. Press play!

### Desktop Software:
- **Mac**: GarageBand (free), Logic Pro
- **Windows/Mac**: FL Studio, Ableton Live, Reaper
- **Free/Open**: MuseScore, LMMS, Ardour

### Convert to MP3:
```bash
# Using MuseScore (free)
mscore sound_maps/your_file.mid -o output.mp3

# Using timidity (Linux)
timidity sound_maps/your_file.mid -Ow -o output.wav
```

## 🎼 How It Works

### Musical Mapping

#### Road Types → Instruments:
- **Motorways/Highways** → Acoustic Bass (deep, sustained)
- **Primary Roads** → Piano (clear, rhythmic)
- **Secondary Roads** → Electric Piano (mid-range)
- **Tertiary Roads** → String Ensemble (flowing)
- **Residential Streets** → Acoustic Guitar (gentle, melodic)

#### Road Types → Pitch:
- **Motorways** → Low bass notes (C2-G2)
- **Primary** → Mid bass (C3-G3)
- **Secondary** → Mid range (G3-D4)
- **Tertiary** → Higher mid (C4-G4)
- **Residential** → Melody range (G4-D5)

#### Street Length → Note Duration:
- Short streets (50m) → Quick notes (0.25 beats)
- Medium streets (200m) → Normal notes (0.5 beats)
- Long streets (500m+) → Sustained notes (1-2 beats)

#### Intersections → Percussion:
- 4+ way intersections → Closed Hi-Hat (prominent beat)
- 3-way intersections → Open Hi-Hat (lighter accent)

### Advanced Features

#### Water Features:
- **Rivers/Streams** → Flowing ocarina notes
- **Lakes/Ponds** → Sustained ambient pads

#### Parks:
- **Bird sounds** → High-pitched chirps
- **Wind** → Soft, sustained pads

#### Musical Intelligence:
- **Scale quantization** - All notes snap to chosen scale
- **Harmonic progressions** - Background chord changes
- **Bass drones** - Grounding low frequencies

## 📊 Recommended Settings by City Type

### Dense, Organic Cities (Tokyo, Mumbai, Marrakech):
```bash
# Random walk captures the chaos beautifully
-m random_walk -d 6000-8000 -t 130-150
```

### Grid Cities (Manhattan, Barcelona):
```bash
# Grid scan emphasizes the structure
-m grid_scan -d 5000-7000 -t 110-120
```

### Water Cities (Venice, Amsterdam):
```bash
# Advanced version captures water sounds
# Use minor or pentatonic for contemplative mood
-s minor -d 3000-5000 -t 80-100
```

### Historic Cities (Rome, Paris):
```bash
# Depth-first explores winding streets
-m depth_first -d 4000-6000 -t 90-110
```

## 🎯 Distance Guide

- **3,000-4,000m** - Small area, intimate soundscape (2-3 minutes)
- **5,000-6,000m** - Medium area, balanced composition (3-5 minutes)
- **7,000-10,000m** - Large area, epic journey (5-8 minutes)
- **10,000m+** - Might be slow to download and very long compositions

## 🎨 Creative Ideas

### 1. City Comparison
Generate sounds for multiple cities and compare:
```bash
python create_sound_map.py -c "Tokyo" -C "Japan" -m random_walk -d 6000
python create_sound_map.py -c "New York" -C "USA" -m random_walk -d 6000
python create_sound_map.py -c "Paris" -C "France" -m random_walk -d 6000
```

### 2. Same City, Different Modes
Hear how traversal changes the music:
```bash
python create_sound_map.py -c "Venice" -C "Italy" -m grid_scan -d 4000
python create_sound_map.py -c "Venice" -C "Italy" -m random_walk -d 4000
python create_sound_map.py -c "Venice" -C "Italy" -m depth_first -d 4000
```

### 3. Scale Exploration
Try all musical moods for your city:
```bash
python create_sound_map_advanced.py -c "Mumbai" -C "India" -s major -d 6000
python create_sound_map_advanced.py -c "Mumbai" -C "India" -s minor -d 6000
python create_sound_map_advanced.py -c "Mumbai" -C "India" -s pentatonic -d 6000
python create_sound_map_advanced.py -c "Mumbai" -C "India" -s blues -d 6000
```

### 4. Tempo Variations
Change the energy:
```bash
# Slow, meditative
python create_sound_map_advanced.py -c "Kyoto" -C "Japan" -s pentatonic -t 70

# Normal pace
python create_sound_map_advanced.py -c "Kyoto" -C "Japan" -s pentatonic -t 100

# Fast, energetic
python create_sound_map_advanced.py -c "Kyoto" -C "Japan" -s pentatonic -t 150
```

## 🐛 Troubleshooting

### "No module named 'MIDIUtil'"
```bash
pip install MIDIUtil
```

### Generation is slow
- Reduce `-d` distance (try 3000-5000m)
- Smaller cities generate faster
- First download takes longer (OSM data fetching)

### MIDI file won't play
- Make sure you have MIDI player software installed
- Try the online player: https://signal.vercel.app/edit
- MIDI files need to be "rendered" - they're not audio files

### City not found
- Check spelling
- Try different country names ("USA" vs "United States")
- Be specific: "Mumbai, India" not just "Mumbai"

## 🎓 Understanding the Code

### Key Classes:

**`CityMusician`** (Basic version)
- Manages MIDI file creation
- Maps streets to musical parameters
- Handles traversal algorithms

**`AdvancedCityMusician`** (Advanced version)
- Extends basic version
- Adds water and park layers
- Implements musical scales
- Creates harmonic progressions

### Key Functions:

- `road_type_to_pitch()` - Converts street type to MIDI note
- `add_note_from_edge()` - Turns one street into one note
- `traverse_random_walk()` - Generates composition via random walk
- `quantize_to_scale()` - Snaps notes to musical scale

## 🚀 Next Steps

### Ideas to Extend:

1. **Add building height data** → Volume/dynamics
2. **Time-of-day variations** → Morning vs. evening soundscapes
3. **Population density** → Note density/rhythm
4. **Historical data** → Show city evolution through sound
5. **Live GPS tracking** → Generate music as you walk
6. **AI melody generation** → Use street patterns as seed for ML
7. **Export to DAW** → Import into Ableton/FL Studio for mixing
8. **Visual sync** → Sync music with animated map poster

### Contributing:

This is an open-ended creative project. Experiment with:
- Different instrument mappings
- New traversal algorithms
- Alternative musical scales
- Integration with other data sources

## 📝 Technical Notes

- Uses **General MIDI** standard (128 instruments)
- MIDI channels: 0-15 (channel 9 is percussion)
- Note range: 0-127 (C-1 to G9)
- Tempo range: 40-240 BPM recommended
- Generated files are typically 50-500KB

## 🎵 Fun Facts

- A typical 5km radius city generates 500-2000 notes
- Random walk mode creates the most "musical" results
- Grid scan sounds more mechanical/industrial
- Water cities sound more contemplative
- Grid cities sound more rhythmic

---

**Made with 🎵 by converting OpenStreetMap data into music**

Have fun making your city sing! 🌆🎼