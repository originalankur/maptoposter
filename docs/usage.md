# Usage

## Basic Command

```bash
python create_map_poster.py --city <city> --country <country> [options]
```

## Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--city` | `-c` | City name | required |
| `--country` | `-C` | Country name | required |
| `--theme` | `-t` | Theme name | feature_based |
| `--distance` | `-d` | Map radius in meters | 29000 |
| `--list-themes` | | List all available themes | |

## Examples

### Iconic Grid Patterns

```bash
# Manhattan grid
python create_map_poster.py -c "New York" -C "USA" -t noir -d 12000

# Eixample district
python create_map_poster.py -c "Barcelona" -C "Spain" -t warm_beige -d 8000
```

### Waterfront & Canals

```bash
# Canal network
python create_map_poster.py -c "Venice" -C "Italy" -t blueprint -d 4000

# Concentric canals
python create_map_poster.py -c "Amsterdam" -C "Netherlands" -t ocean -d 6000

# Palm & coastline
python create_map_poster.py -c "Dubai" -C "UAE" -t midnight_blue -d 15000
```

### Radial Patterns

```bash
# Haussmann boulevards
python create_map_poster.py -c "Paris" -C "France" -t pastel_dream -d 10000

# Ring roads
python create_map_poster.py -c "Moscow" -C "Russia" -t noir -d 12000
```

### Organic Old Cities

```bash
# Dense organic streets
python create_map_poster.py -c "Tokyo" -C "Japan" -t japanese_ink -d 15000

# Medina maze
python create_map_poster.py -c "Marrakech" -C "Morocco" -t terracotta -d 5000

# Ancient layout
python create_map_poster.py -c "Rome" -C "Italy" -t warm_beige -d 8000
```

### Coastal Cities

```bash
# Peninsula grid
python create_map_poster.py -c "San Francisco" -C "USA" -t sunset -d 10000

# Harbor city
python create_map_poster.py -c "Sydney" -C "Australia" -t ocean -d 12000

# Coastal peninsula
python create_map_poster.py -c "Mumbai" -C "India" -t contrast_zones -d 18000
```

### River Cities

```bash
# Thames curves
python create_map_poster.py -c "London" -C "UK" -t noir -d 15000

# Danube split
python create_map_poster.py -c "Budapest" -C "Hungary" -t copper_patina -d 8000
```

### List Available Themes

```bash
python create_map_poster.py --list-themes
```

## Distance Guide

| Distance | Best for |
|----------|----------|
| 4000-6000m | Small/dense cities (Venice, Amsterdam center) |
| 8000-12000m | Medium cities, focused downtown (Paris, Barcelona) |
| 15000-20000m | Large metros, full city view (Tokyo, Mumbai) |
