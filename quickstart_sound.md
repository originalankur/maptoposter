# 🚀 Sound Maps - Quick Start Guide

Get your first city sound map in 5 minutes!

## Step 1: Install (30 seconds)

```bash
pip install MIDIUtil
```

## Step 2: Generate Your First Sound Map (2-3 minutes)

```bash
# Basic version - simple and fast
python create_sound_map.py -c "Venice" -C "Italy" -d 3000

# Advanced version - richer sound with water and parks
python create_sound_map_advanced.py -c "Venice" -C "Italy" -d 3000 -s pentatonic
```

## Step 3: Listen! (1 minute)

### Option A: Online (Easiest)
1. Go to **https://signal.vercel.app/edit**
2. Drag your `.mid` file from `sound_maps/` folder
3. Press ▶️ Play!

### Option B: Desktop
- **Mac**: Open with GarageBand
- **Windows**: Use MuseScore (free) or FL Studio
- **Any OS**: VLC Media Player can play MIDI files

---

## 🎵 Try These Next

### Your Hometown
```bash
python create_sound_map.py -c "Mumbai" -C "India" -d 6000 -m random_walk
```

### Different Moods (Advanced Version)
```bash
# Peaceful Asian vibe
python create_sound_map_advanced.py -c "Kyoto" -C "Japan" -s pentatonic -d 5000 -t 90

# Melancholic European
python create_sound_map_advanced.py -c "Venice" -C "Italy" -s minor -d 4000 -t 80

# Energetic American
python create_sound_map_advanced.py -c "New York" -C "USA" -s major -d 5000 -t 130
```

### Batch Generate Multiple Cities
```bash
# Generate sounds for all world capitals at once
python batch_sound_generator.py -coll world_capitals -v advanced

# See all available collections
python batch_sound_generator.py --list
```

---

## 🎛️ Quick Parameter Guide

### Distance (`-d`)
- `3000` = Small area, short song (~2 min)
- `5000` = Medium area, good balance (~3-4 min)
- `8000` = Large area, long composition (~6-8 min)

### Tempo (`-t`)
- `80` = Slow, meditative
- `120` = Normal walking pace
- `150` = Fast, energetic

### Mode (`-m`) - Basic Version Only
- `random_walk` = Organic, flowing (most musical)
- `grid_scan` = Structured, systematic
- `depth_first` = Exploratory

### Scale (`-s`) - Advanced Version Only
- `pentatonic` = Asian, peaceful
- `major` = Happy, bright
- `minor` = Sad, contemplative
- `blues` = Groovy
- `dorian` = Jazz, medieval

---

## 🎨 Creative Combos to Try

### Water City Meditation
```bash
python create_sound_map_advanced.py -c "Amsterdam" -C "Netherlands" -s minor -d 4000 -t 70
```

### Tokyo Cyberpunk
```bash
python create_sound_map_advanced.py -c "Tokyo" -C "Japan" -s pentatonic -d 8000 -t 150
```

### Mumbai Energy
```bash
python create_sound_map_advanced.py -c "Mumbai" -C "India" -s major -d 7000 -t 135
```

### Paris Romance
```bash
python create_sound_map_advanced.py -c "Paris" -C "France" -s major -d 5000 -t 100
```

---

## 🐛 Common Issues

**"Can't find city"**
→ Check spelling, try full country name

**"Generation is slow"**
→ Reduce distance: try `-d 3000`

**"Can't play MIDI"**
→ Use online player: https://signal.vercel.app/edit

**"ImportError: MIDIUtil"**
→ Run: `pip install MIDIUtil`

---

## 🎓 What's Actually Happening?

1. **Download**: Script fetches real street data from OpenStreetMap
2. **Map**: Each street becomes a musical note
   - Highway = deep bass
   - Small street = high melody
   - Long street = long note
   - Short street = quick note
3. **Export**: Saves as MIDI file (universal music format)
4. **Play**: Open in any music software!

---

## 📁 File Locations

All generated MIDI files go to: `sound_maps/`

Filename format: `{city}_{mode}_{tempo}_{timestamp}.mid`

Example: `mumbai_random_walk_tempo120_20250119_153045.mid`

---

## 🚀 Level Up

Once you're comfortable:

1. **Compare cities**: Generate 5 cities, compare their sounds
2. **Same city, all modes**: Hear how traversal changes music
3. **All scales**: Try all 5 musical scales for one city
4. **Batch generate**: Create a whole collection overnight
5. **Edit in DAW**: Import to FL Studio/Ableton for mixing

---

## 💡 Pro Tips

- Start with **small distances** (3000-5000m) for faster testing
- **Water cities** sound amazing with minor/pentatonic scales
- **Grid cities** work well with grid_scan mode
- **Advanced version** is worth the extra minute for richer sound
- Lower tempo (80-90) = more contemplative
- Higher tempo (130-150) = more energetic

---

**That's it! You're now a Sound Map creator. Have fun! 🎵**

Share your creations and tag them #CitySound or #UrbanSymphony
