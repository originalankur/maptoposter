import os
import json

# Assuming the themes are in a 'themes' folder one level up from the MapPosterStudio folder,
# similar to where create_map_poster.py expects them.
# Structure:
# ProjectRoot/
#   themes/
#   create_map_poster.py
#   MapPosterStudio/
#     poster_engine/
#       themes.py

def get_themes_dir():
    # Go up two levels from this file: poster_engine -> MapPosterStudio -> ProjectRoot
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, 'themes')

def get_available_themes():
    """
    Scans the themes directory and returns a list of available theme names.
    """
    themes_dir = get_themes_dir()
    if not os.path.exists(themes_dir):
        return ["feature_based"] # Fallback
    
    themes = []
    for file in sorted(os.listdir(themes_dir)):
        if file.endswith('.json'):
            theme_name = file[:-5]  # Remove .json extension
            themes.append(theme_name)
    
    if not themes:
        return ["feature_based"]
        
    return themes

def get_theme_details(theme_name):
    """
    Returns the loaded JSON dict for a theme, or None if not found.
    """
    themes_dir = get_themes_dir()
    theme_file = os.path.join(themes_dir, f"{theme_name}.json")
    
    if not os.path.exists(theme_file):
        return None
        
    try:
        with open(theme_file, 'r') as f:
            return json.load(f)
    except:
        return None
