"""
Batch Sound Map Generator
Generate sound maps for multiple cities in one go.
Perfect for creating a "world tour" of city sounds.
"""

import subprocess
import time
import os
from datetime import datetime

# Predefined city collections
CITY_COLLECTIONS = {
    'world_capitals': [
        ('Tokyo', 'Japan', 6000),
        ('Paris', 'France', 5000),
        ('London', 'UK', 6000),
        ('New York', 'USA', 5000),
        ('Mumbai', 'India', 7000),
        ('Cairo', 'Egypt', 5000),
        ('Sydney', 'Australia', 6000),
        ('Moscow', 'Russia', 6000),
    ],
    
    'water_cities': [
        ('Venice', 'Italy', 3000),
        ('Amsterdam', 'Netherlands', 4000),
        ('Stockholm', 'Sweden', 5000),
        ('Copenhagen', 'Denmark', 4000),
        ('Singapore', 'Singapore', 5000),
    ],
    
    'grid_cities': [
        ('New York', 'USA', 5000),
        ('Barcelona', 'Spain', 5000),
        ('Chicago', 'USA', 6000),
        ('Melbourne', 'Australia', 5000),
    ],
    
    'organic_cities': [
        ('Tokyo', 'Japan', 6000),
        ('Marrakech', 'Morocco', 4000),
        ('Rome', 'Italy', 5000),
        ('Athens', 'Greece', 5000),
    ],
    
    'indian_cities': [
        ('Mumbai', 'India', 7000),
        ('Delhi', 'India', 7000),
        ('Bangalore', 'India', 6000),
        ('Chennai', 'India', 6000),
        ('Kolkata', 'India', 6000),
        ('Jaipur', 'India', 5000),
    ],
}

def generate_sound_map(city, country, distance, mode='random_walk', tempo=120, version='basic'):
    """
    Generate a single sound map.
    
    Args:
        city: City name
        country: Country name
        distance: Radius in meters
        mode: Traversal mode
        tempo: BPM
        version: 'basic' or 'advanced'
    """
    if version == 'basic':
        cmd = [
            'python', 'create_sound_map.py',
            '-c', city,
            '-C', country,
            '-m', mode,
            '-d', str(distance),
            '-t', str(tempo)
        ]
    else:  # advanced
        cmd = [
            'python', 'create_sound_map_advanced.py',
            '-c', city,
            '-C', country,
            '-s', 'pentatonic',  # Default scale
            '-d', str(distance),
            '-t', str(tempo)
        ]
    
    print(f"\n{'='*70}")
    print(f"🎵 Generating: {city}, {country}")
    print(f"   Distance: {distance}m | Tempo: {tempo} BPM | Mode: {mode}")
    print(f"{'='*70}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ Successfully generated sound map for {city}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to generate {city}: {e}")
        return False

def batch_generate(collection_name, mode='random_walk', tempo=120, version='basic', delay=5):
    """
    Generate sound maps for a collection of cities.
    
    Args:
        collection_name: Name of city collection
        mode: Traversal mode
        tempo: BPM
        version: 'basic' or 'advanced'
        delay: Seconds to wait between generations (be nice to OSM servers)
    """
    if collection_name not in CITY_COLLECTIONS:
        print(f"❌ Collection '{collection_name}' not found.")
        print(f"Available collections: {', '.join(CITY_COLLECTIONS.keys())}")
        return
    
    cities = CITY_COLLECTIONS[collection_name]
    
    print("\n" + "="*70)
    print(f"🌍 BATCH SOUND MAP GENERATOR")
    print("="*70)
    print(f"Collection: {collection_name}")
    print(f"Cities: {len(cities)}")
    print(f"Version: {version}")
    print(f"Mode: {mode}")
    print(f"Tempo: {tempo} BPM")
    print("="*70)
    
    successful = 0
    failed = 0
    start_time = time.time()
    
    for i, (city, country, distance) in enumerate(cities, 1):
        print(f"\n[{i}/{len(cities)}] Processing {city}...")
        
        success = generate_sound_map(city, country, distance, mode, tempo, version)
        
        if success:
            successful += 1
        else:
            failed += 1
        
        # Wait between requests (be respectful to OSM)
        if i < len(cities):
            print(f"⏳ Waiting {delay} seconds before next city...")
            time.sleep(delay)
    
    elapsed = time.time() - start_time
    
    # Summary
    print("\n" + "="*70)
    print("📊 BATCH GENERATION COMPLETE")
    print("="*70)
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"⏱️  Total time: {elapsed/60:.1f} minutes")
    print(f"📁 Files saved in: sound_maps/")
    print("="*70)

def custom_batch(cities_list, mode='random_walk', tempo=120, version='basic'):
    """
    Generate sound maps for a custom list of cities.
    
    Args:
        cities_list: List of (city, country, distance) tuples
        mode: Traversal mode
        tempo: BPM
        version: 'basic' or 'advanced'
    """
    print("\n" + "="*70)
    print(f"🎨 CUSTOM BATCH GENERATION")
    print("="*70)
    print(f"Cities: {len(cities_list)}")
    print("="*70)
    
    for city, country, distance in cities_list:
        generate_sound_map(city, country, distance, mode, tempo, version)
        time.sleep(5)
    
    print("\n✅ Custom batch complete!")

def list_collections():
    """Display all available city collections."""
    print("\n" + "="*70)
    print("🌍 AVAILABLE CITY COLLECTIONS")
    print("="*70)
    
    for name, cities in CITY_COLLECTIONS.items():
        print(f"\n{name}:")
        for city, country, dist in cities:
            print(f"  • {city}, {country} ({dist}m)")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Batch generate sound maps for multiple cities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate for all world capitals
  python batch_sound_generator.py -coll world_capitals
  
  # Water cities with advanced version
  python batch_sound_generator.py -coll water_cities -v advanced
  
  # Indian cities with blues scale (requires advanced)
  python batch_sound_generator.py -coll indian_cities -v advanced -t 110
  
  # List all available collections
  python batch_sound_generator.py --list
  
  # Custom cities (edit the script to add your own list)
  
Available Collections:
  world_capitals  - Major world capitals (8 cities)
  water_cities    - Cities with canals/waterways (5 cities)
  grid_cities     - Cities with grid patterns (4 cities)
  organic_cities  - Organically grown cities (4 cities)
  indian_cities   - Major Indian metros (6 cities)
        """
    )
    
    parser.add_argument('--collection', '-coll', type=str, 
                       help='City collection name')
    parser.add_argument('--mode', '-m', type=str, default='random_walk',
                       choices=['grid_scan', 'random_walk', 'depth_first'],
                       help='Traversal mode (default: random_walk)')
    parser.add_argument('--tempo', '-t', type=int, default=120,
                       help='Tempo in BPM (default: 120)')
    parser.add_argument('--version', '-v', type=str, default='basic',
                       choices=['basic', 'advanced'],
                       help='Generator version (default: basic)')
    parser.add_argument('--delay', '-d', type=int, default=5,
                       help='Delay between cities in seconds (default: 5)')
    parser.add_argument('--list', action='store_true',
                       help='List all available collections')
    
    args = parser.parse_args()
    
    if args.list:
        list_collections()
    elif args.collection:
        batch_generate(
            args.collection,
            mode=args.mode,
            tempo=args.tempo,
            version=args.version,
            delay=args.delay
        )
    else:
        print("Please specify --collection or --list")
        parser.print_help()

# You can also import this and use it programmatically:
# from batch_sound_generator import custom_batch
# 
# my_cities = [
#     ('Paris', 'France', 5000),
#     ('Rome', 'Italy', 5000),
#     ('Barcelona', 'Spain', 5000),
# ]
# 
# custom_batch(my_cities, mode='random_walk', tempo=110, version='advanced')
