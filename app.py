import os
import glob
import subprocess
from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__)

BASE_DIR = os.getcwd()
POSTER_DIR = os.path.join(BASE_DIR, 'posters')
THEME_DIR = os.path.join(BASE_DIR, 'themes')
os.makedirs(POSTER_DIR, exist_ok=True)

@app.route('/')
def index():
    themes = []
    # List themes from the cloned directory
    if os.path.exists(THEME_DIR):
        files = glob.glob(os.path.join(THEME_DIR, "*.json"))
        themes = [os.path.basename(f).replace(".json", "") for f in files]
    if not themes: themes = ["feature_based", "gradient_roads", "noir", "dark", "light"]
    return render_template('index.html', themes=themes)

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    city = data.get('city')
    country = data.get('country')
    theme = data.get('theme')
    radius = str(data.get('radius', 15000))

    if not city or not country:
        return jsonify({'success': False, 'error': 'City and Country required.'})

    # Call the original script present in the clone
    cmd = ["python", "create_map_poster.py", "--city", city, "--country", country, "--distance", radius, "--theme", theme]

    try:
        existing_files = set(glob.glob(os.path.join(POSTER_DIR, "*.png")))
        # 5-minute timeout
        subprocess.run(cmd, check=True, timeout=300)
        
        current_files = set(glob.glob(os.path.join(POSTER_DIR, "*.png")))
        new_files = list(current_files - existing_files)

        if new_files:
            latest_file = max(new_files, key=os.path.getctime)
            return jsonify({'success': True, 'filename': os.path.basename(latest_file)})
        else:
            return jsonify({'success': False, 'error': 'Script finished but no image file found.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/posters/<path:filename>')
def serve_poster(filename):
    return send_from_directory(POSTER_DIR, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5025)