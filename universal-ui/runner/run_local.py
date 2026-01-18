#!/usr/bin/env python3
"""
Local Runner for Maptoposter - DUAL MODE
==========================================

MODE 1 (CLI): Generate posters via command line
Usage: python run_local.py --city "Berlin" --theme "noir"

MODE 2 (SERVER): Run as localhost HTTP server for web UI
Usage: python run_local.py --serve

This script calls create_map_poster.py ONLY as a subprocess.
Does NOT import or modify the core logic.
"""

import subprocess
import sys
import os
import argparse
import json
from pathlib import Path


def get_project_root():
    """Get the project root directory (two levels up from this script)."""
    return Path(__file__).parent.parent.parent.resolve()


def get_available_themes():
    """
    Get list of available themes from the themes directory.
    
    Returns:
        list: Theme names (without .json extension)
    """
    project_root = get_project_root()
    themes_dir = project_root / "themes"
    
    if not themes_dir.exists():
        return []
    
    themes = []
    for theme_file in themes_dir.glob("*.json"):
        themes.append(theme_file.stem)
    
    return sorted(themes)


def validate_city(city):
    """Validate city input."""
    if not city or not city.strip():
        return False
    return True


def validate_theme(theme):
    """Validate theme exists."""
    if not theme:
        return True, ""  # Theme is optional
    
    available_themes = get_available_themes()
    if theme not in available_themes:
        return False, f"Theme '{theme}' not found. Available: {', '.join(available_themes)}"
    
    return True, ""


def run_poster_generator(city, country=None, theme=None, radius=None):
    """
    Run the main create_map_poster.py script as a subprocess.
    
    Args:
        city: City name (required)
        country: Country name (optional)
        theme: Theme name (optional)
        radius: Map radius in meters (optional, not yet supported by core)
    
    Returns:
        tuple: (success: bool, output_path: str or None, error_message: str or None)
    """
    project_root = get_project_root()
    main_script = project_root / "create_map_poster.py"
    
    if not main_script.exists():
        return False, None, f"Main script not found at {main_script}"
    
    # Build command
    cmd = [sys.executable, str(main_script), "--city", city]
    
    # Add country (required by main script)
    if country:
        cmd.extend(["--country", country])
    else:
        # Default to city name if no country provided
        cmd.extend(["--country", city])
    
    # Add theme if specified
    if theme:
        cmd.extend(["--theme", theme])
    
    # Note: radius support would require updating the core script
    # For now, we document it but don't pass it
    
    try:
        # Run subprocess
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Forward output to stderr (non-critical info)
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        if result.returncode == 0:
            # Find the most recent poster
            output_path = find_latest_poster()
            if output_path:
                return True, output_path, None
            else:
                return False, None, "Poster generation completed but output file not found"
        else:
            return False, None, f"Generation failed with exit code {result.returncode}"
    
    except subprocess.TimeoutExpired:
        return False, None, "Generation timed out after 5 minutes"
    except Exception as e:
        return False, None, f"Unexpected error: {str(e)}"


def find_latest_poster():
    """Find the most recently created poster in the posters directory."""
    project_root = get_project_root()
    posters_dir = project_root / "posters"
    
    if not posters_dir.exists():
        return None
    
    poster_files = list(posters_dir.glob("*.png"))
    if not poster_files:
        return None
    
    # Return the most recently modified file
    latest = max(poster_files, key=lambda p: p.stat().st_mtime)
    return str(latest.absolute())


# ==================== CLI MODE ====================

def cli_mode(args):
    """Run in CLI mode - generate poster via command line."""
    # Validate city
    if not validate_city(args.city):
        print("ERROR: City name cannot be empty", file=sys.stderr)
        sys.exit(1)
    
    # Validate theme if provided
    theme_valid, theme_message = validate_theme(args.theme)
    if not theme_valid:
        print(f"ERROR: {theme_message}", file=sys.stderr)
        sys.exit(1)
    
    # Run the generator
    success, output_path, error_message = run_poster_generator(
        city=args.city,
        country=args.country,
        theme=args.theme,
        radius=args.radius
    )
    
    if success:
        # Print ONLY the output path to stdout (clean output for parsing)
        print(output_path)
        sys.exit(0)
    else:
        # Print error to stderr
        print(f"ERROR: {error_message}", file=sys.stderr)
        sys.exit(1)


# ==================== SERVER MODE ====================

def server_mode(args):
    """Run in server mode - start localhost HTTP server."""
    try:
        from flask import Flask, request, jsonify
        from flask_cors import CORS
    except ImportError:
        print("ERROR: Flask not installed. Install with: pip install flask flask-cors", file=sys.stderr)
        sys.exit(1)
    
    app = Flask(__name__)
    CORS(app)  # Enable CORS for local browser access
    
    @app.route('/health', methods=['GET'])
    def health():
        """Health check endpoint."""
        return jsonify({"status": "ok", "mode": "server"})
    
    @app.route('/themes', methods=['GET'])
    def themes():
        """Get available themes."""
        available_themes = get_available_themes()
        return jsonify({"themes": available_themes})
    
    @app.route('/generate', methods=['POST'])
    def generate():
        """Generate poster endpoint."""
        data = request.get_json()
        
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        city = data.get('city', '').strip()
        country = data.get('country', '').strip()
        theme = data.get('theme', '').strip()
        radius = data.get('radius')
        
        # Validate city
        if not validate_city(city):
            return jsonify({"status": "error", "message": "City name is required"}), 400
        
        # Validate theme
        if theme:
            theme_valid, theme_message = validate_theme(theme)
            if not theme_valid:
                return jsonify({"status": "error", "message": theme_message}), 400
        
        # Run generator
        success, output_path, error_message = run_poster_generator(
            city=city,
            country=country if country else None,
            theme=theme if theme else None,
            radius=radius
        )
        
        if success:
            return jsonify({
                "status": "ok",
                "message": "Poster generated successfully",
                "image_path": output_path
            })
        else:
            return jsonify({
                "status": "error",
                "message": error_message or "Unknown error occurred"
            }), 500
    
    # Get host and port from args or use defaults
    host = args.host if hasattr(args, 'host') else '127.0.0.1'
    port = args.port if hasattr(args, 'port') else 8000
    
    print(f"""
╔════════════════════════════════════════════════════════════╗
║  Maptoposter Local Server                                  ║
╠════════════════════════════════════════════════════════════╣
║  Server running at: http://{host}:{port}                 ║
║                                                            ║
║  Endpoints:                                                ║
║    GET  /health   - Health check                          ║
║    GET  /themes   - List available themes                 ║
║    POST /generate - Generate poster                       ║
║                                                            ║
║  Open web UI: universal-ui/web/index.html                 ║
║  Press Ctrl+C to stop                                     ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host=host, port=port, debug=False)


# ==================== MAIN ====================

def main():
    """Main entry point for the local runner."""
    parser = argparse.ArgumentParser(
        description="Local runner for maptoposter - DUAL MODE (CLI or Server)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
MODE 1 - CLI (Command Line Interface):
  python run_local.py --city "Berlin" --theme "noir"
  python run_local.py --city "Tokyo" --country "Japan" --theme "ocean"

MODE 2 - SERVER (Localhost HTTP Server):
  python run_local.py --serve
  python run_local.py --serve --port 8080

Then open: universal-ui/web/index.html in your browser
        """
    )
    
    # Server mode flag
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start localhost HTTP server mode (for automatic web UI generation)"
    )
    
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Server host (default: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Server port (default: 8000)"
    )
    
    # CLI mode arguments
    parser.add_argument(
        "--city",
        help="City name (required for CLI mode)"
    )
    
    parser.add_argument(
        "--country",
        help="Country name (optional)"
    )
    
    parser.add_argument(
        "--theme",
        help="Theme name (optional, e.g., noir, ocean, midnight_blue)"
    )
    
    parser.add_argument(
        "--radius",
        type=int,
        help="Map radius in meters (optional, not yet supported by core script)"
    )
    
    args = parser.parse_args()
    
    # Determine mode
    if args.serve:
        # SERVER MODE
        server_mode(args)
    else:
        # CLI MODE (default)
        if not args.city:
            parser.error("--city is required for CLI mode (use --serve for server mode)")
        cli_mode(args)


if __name__ == "__main__":
    main()
