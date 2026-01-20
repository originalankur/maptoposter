"""
Example Usage Script
Shows how to use the sound map generators programmatically.
Perfect for custom workflows and automation.
"""

import osmnx as ox
from create_sound_map import CityMusician, get_coordinates
from create_sound_map_advanced import AdvancedCityMusician
import os

def example_1_basic_generation():
    """
    Example 1: Basic sound map generation
    """
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Sound Map")
    print("="*60)
    
    # Get coordinates
    city, country = "Venice", "Italy"
    coords = get_coordinates(city, country)
    
    # Download street network
    print(f"Downloading street network for {city}...")
    G = ox.graph_from_point(coords, dist=3000, dist_type='bbox', network_type='all')
    
    # Create musician and compose
    musician = CityMusician(G, mode='random_walk', tempo=100)
    musician.compose()
    
    # Save
    output = "sound_maps/example_1_venice.mid"
    musician.save(output)
    
    print(f"✅ Created: {output}")

def example_2_compare_modes():
    """
    Example 2: Generate same city with all 3 modes
    Compare how traversal affects the music
    """
    print("\n" + "="*60)
    print("EXAMPLE 2: Compare Traversal Modes")
    print("="*60)
    
    city, country = "Paris", "France"
    coords = get_coordinates(city, country)
    
    print("Downloading street network...")
    G = ox.graph_from_point(coords, dist=4000, dist_type='bbox', network_type='all')
    
    modes = ['grid_scan', 'random_walk', 'depth_first']
    
    for mode in modes:
        print(f"\nGenerating with {mode} mode...")
        musician = CityMusician(G, mode=mode, tempo=110)
        musician.compose()
        output = f"sound_maps/example_2_paris_{mode}.mid"
        musician.save(output)
        print(f"✅ Created: {output}")
    
    print("\n🎵 Now compare the three files to hear the difference!")

def example_3_advanced_with_features():
    """
    Example 3: Advanced version with water and parks
    """
    print("\n" + "="*60)
    print("EXAMPLE 3: Advanced with Environmental Sounds")
    print("="*60)
    
    city, country = "Amsterdam", "Netherlands"
    coords = get_coordinates(city, country)
    
    # Download street network
    print("Downloading street network...")
    G = ox.graph_from_point(coords, dist=4000, dist_type='bbox', network_type='all')
    
    # Download water features
    print("Downloading water features...")
    try:
        water = ox.features_from_point(coords, tags={'natural': 'water', 'waterway': True}, dist=4000)
        print(f"Found {len(water)} water features")
    except:
        water = None
        print("No water features found")
    
    # Download parks
    print("Downloading parks...")
    try:
        parks = ox.features_from_point(coords, tags={'leisure': 'park'}, dist=4000)
        print(f"Found {len(parks)} parks")
    except:
        parks = None
        print("No parks found")
    
    # Create advanced musician
    musician = AdvancedCityMusician(G, water, parks, mode='random_walk', tempo=90)
    musician.set_scale('minor')  # Contemplative mood
    musician.compose()
    
    output = "sound_maps/example_3_amsterdam_advanced.mid"
    musician.save(output)
    
    print(f"✅ Created: {output}")

def example_4_all_scales():
    """
    Example 4: Generate one city in all musical scales
    """
    print("\n" + "="*60)
    print("EXAMPLE 4: Explore All Musical Scales")
    print("="*60)
    
    city, country = "Kyoto", "Japan"
    coords = get_coordinates(city, country)
    
    print("Downloading street network...")
    G = ox.graph_from_point(coords, dist=5000, dist_type='bbox', network_type='all')
    
    # Try all scales
    scales = ['major', 'minor', 'pentatonic', 'blues', 'dorian']
    
    for scale in scales:
        print(f"\nGenerating with {scale} scale...")
        musician = AdvancedCityMusician(G, None, None, mode='random_walk', tempo=100)
        musician.set_scale(scale)
        musician.compose()
        output = f"sound_maps/example_4_kyoto_{scale}.mid"
        musician.save(output)
        print(f"✅ Created: {output}")
    
    print("\n🎵 Listen to all 5 to hear how scale changes the mood!")

def example_5_tempo_variations():
    """
    Example 5: Same city at different tempos
    Feel how tempo affects energy
    """
    print("\n" + "="*60)
    print("EXAMPLE 5: Tempo Variations")
    print("="*60)
    
    city, country = "Mumbai", "India"
    coords = get_coordinates(city, country)
    
    print("Downloading street network...")
    G = ox.graph_from_point(coords, dist=6000, dist_type='bbox', network_type='all')
    
    tempos = [70, 100, 130, 160]  # Slow to very fast
    tempo_names = ['slow', 'normal', 'fast', 'very_fast']
    
    for tempo, name in zip(tempos, tempo_names):
        print(f"\nGenerating at {tempo} BPM ({name})...")
        musician = CityMusician(G, mode='random_walk', tempo=tempo)
        musician.compose()
        output = f"sound_maps/example_5_mumbai_{name}_tempo{tempo}.mid"
        musician.save(output)
        print(f"✅ Created: {output}")
    
    print("\n🎵 Compare tempos: slow meditation vs. fast energy!")

def example_6_custom_musician():
    """
    Example 6: Customize the musician with your own settings
    """
    print("\n" + "="*60)
    print("EXAMPLE 6: Custom Musician Settings")
    print("="*60)
    
    city, country = "Tokyo", "Japan"
    coords = get_coordinates(city, country)
    
    print("Downloading street network...")
    G = ox.graph_from_point(coords, dist=6000, dist_type='bbox', network_type='all')
    
    # Create custom musician
    musician = AdvancedCityMusician(G, None, None, mode='random_walk', tempo=120)
    
    # Customize: use blues scale
    musician.set_scale('blues')
    
    # You could also modify:
    # - musician.instruments (change which instruments are used)
    # - musician.tracks (add more tracks)
    # - musician.current_scale (custom scale intervals)
    
    musician.compose()
    
    output = "sound_maps/example_6_tokyo_custom.mid"
    musician.save(output)
    
    print(f"✅ Created: {output}")

def example_7_city_comparison():
    """
    Example 7: Compare 3 very different cities
    """
    print("\n" + "="*60)
    print("EXAMPLE 7: City Comparison")
    print("="*60)
    
    cities = [
        ("Manhattan", "USA", 5000),        # Grid city
        ("Venice", "Italy", 3000),         # Water city
        ("Tokyo", "Japan", 6000),          # Organic city
    ]
    
    for city, country, dist in cities:
        print(f"\nProcessing {city}...")
        coords = get_coordinates(city, country)
        G = ox.graph_from_point(coords, dist=dist, dist_type='bbox', network_type='all')
        
        musician = CityMusician(G, mode='random_walk', tempo=120)
        musician.compose()
        
        city_slug = city.lower().replace(' ', '_')
        output = f"sound_maps/example_7_compare_{city_slug}.mid"
        musician.save(output)
        print(f"✅ Created: {output}")
    
    print("\n🎵 Compare: Grid vs. Water vs. Organic street patterns!")

def run_all_examples():
    """Run all examples in sequence."""
    print("\n" + "="*60)
    print("🎵 RUNNING ALL EXAMPLES")
    print("="*60)
    print("\nThis will generate ~20 MIDI files.")
    print("Total time: ~15-20 minutes")
    print("\nPress Ctrl+C to cancel, or Enter to continue...")
    input()
    
    examples = [
        ("Basic Generation", example_1_basic_generation),
        ("Compare Modes", example_2_compare_modes),
        ("Advanced Features", example_3_advanced_with_features),
        ("All Scales", example_4_all_scales),
        ("Tempo Variations", example_5_tempo_variations),
        ("Custom Settings", example_6_custom_musician),
        ("City Comparison", example_7_city_comparison),
    ]
    
    for name, func in examples:
        try:
            func()
            print(f"\n✅ {name} complete!")
        except Exception as e:
            print(f"\n❌ {name} failed: {e}")
        
        # Small delay between examples
        print("\nWaiting 3 seconds before next example...")
        import time
        time.sleep(3)
    
    print("\n" + "="*60)
    print("🎉 ALL EXAMPLES COMPLETE!")
    print("="*60)
    print(f"\nCheck the sound_maps/ folder for all generated files!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run example sound map generations")
    parser.add_argument('--example', '-e', type=int, choices=range(1, 8),
                       help='Run specific example (1-7)')
    parser.add_argument('--all', action='store_true',
                       help='Run all examples')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs('sound_maps', exist_ok=True)
    
    if args.all:
        run_all_examples()
    elif args.example:
        examples = [
            example_1_basic_generation,
            example_2_compare_modes,
            example_3_advanced_with_features,
            example_4_all_scales,
            example_5_tempo_variations,
            example_6_custom_musician,
            example_7_city_comparison,
        ]
        examples[args.example - 1]()
    else:
        # Interactive menu
        print("\n" + "="*60)
        print("🎵 SOUND MAP EXAMPLES")
        print("="*60)
        print("\nChoose an example to run:")
        print("\n1. Basic Generation (Venice)")
        print("2. Compare Modes (Paris in 3 modes)")
        print("3. Advanced Features (Amsterdam with water)")
        print("4. All Scales (Kyoto in 5 scales)")
        print("5. Tempo Variations (Mumbai at 4 tempos)")
        print("6. Custom Settings (Tokyo customized)")
        print("7. City Comparison (3 different cities)")
        print("\n0. Run ALL examples")
        print("\n" + "="*60)
        
        choice = input("\nEnter number (0-7): ").strip()
        
        if choice == '0':
            run_all_examples()
        elif choice in ['1', '2', '3', '4', '5', '6', '7']:
            examples = [
                example_1_basic_generation,
                example_2_compare_modes,
                example_3_advanced_with_features,
                example_4_all_scales,
                example_5_tempo_variations,
                example_6_custom_musician,
                example_7_city_comparison,
            ]
            examples[int(choice) - 1]()
        else:
            print("Invalid choice!")
