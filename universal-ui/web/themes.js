/**
 * Available Themes
 * 
 * This file contains the list of all available themes for the map poster generator.
 * These themes correspond to the JSON files in the /themes directory.
 * 
 * To update: Add or remove theme names to match the files in /themes/
 */

const AVAILABLE_THEMES = [
    {
        value: "autumn",
        label: "Autumn",
        description: "Warm autumn colors"
    },
    {
        value: "blueprint",
        label: "Blueprint",
        description: "Classic blueprint style"
    },
    {
        value: "contrast_zones",
        label: "Contrast Zones",
        description: "High contrast zones"
    },
    {
        value: "copper_patina",
        label: "Copper Patina",
        description: "Aged copper aesthetic"
    },
    {
        value: "feature_based",
        label: "Feature Based",
        description: "Color by feature type (default)"
    },
    {
        value: "forest",
        label: "Forest",
        description: "Deep forest greens"
    },
    {
        value: "gradient_roads",
        label: "Gradient Roads",
        description: "Roads with gradient colors"
    },
    {
        value: "japanese_ink",
        label: "Japanese Ink",
        description: "Traditional ink painting style"
    },
    {
        value: "midnight_blue",
        label: "Midnight Blue",
        description: "Dark blue night theme"
    },
    {
        value: "monochrome_blue",
        label: "Monochrome Blue",
        description: "Single-color blue theme"
    },
    {
        value: "neon_cyberpunk",
        label: "Neon Cyberpunk",
        description: "Bright neon colors"
    },
    {
        value: "noir",
        label: "Noir",
        description: "Classic black and white"
    },
    {
        value: "ocean",
        label: "Ocean",
        description: "Ocean blues and teals"
    },
    {
        value: "pastel_dream",
        label: "Pastel Dream",
        description: "Soft pastel colors"
    },
    {
        value: "sunset",
        label: "Sunset",
        description: "Warm sunset tones"
    },
    {
        value: "terracotta",
        label: "Terracotta",
        description: "Earthy terracotta"
    },
    {
        value: "warm_beige",
        label: "Warm Beige",
        description: "Neutral warm beige"
    }
];

// Default theme
const DEFAULT_THEME = "feature_based";
