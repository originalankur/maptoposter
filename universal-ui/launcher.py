#!/usr/bin/env python3
"""
Maptoposter Universal Launcher
Cross-platform launcher that starts the server and opens the web UI
"""

import os
import sys
import time
import webbrowser
import subprocess
import platform
from pathlib import Path

# Configuration
SERVER_PORT = 8001
SERVER_HOST = "127.0.0.1"
SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"
WEB_UI_PATH = "web/index.html"


def get_project_root():
    """Get the universal-ui directory."""
    return Path(__file__).parent.resolve()


def check_dependencies():
    """Check if required Python packages are installed."""
    try:
        import flask
        import flask_cors
        return True
    except ImportError:
        return False


def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing required dependencies...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "flask", "flask-cors"],
            check=True,
            capture_output=True
        )
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        print("Please run manually: pip install flask flask-cors")
        return False


def start_server(project_root):
    """Start the Flask server in background."""
    runner_path = project_root / "runner" / "run_local.py"
    
    if not runner_path.exists():
        print(f"❌ Error: Server script not found at {runner_path}")
        return None
    
    print(f"🚀 Starting server on {SERVER_URL}...")
    
    try:
        # Start server process
        process = subprocess.Popen(
            [sys.executable, str(runner_path), "--serve", "--port", str(SERVER_PORT)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=project_root.parent  # Run from maptoposter root
        )
        
        # Wait a bit for server to start
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print(f"❌ Server failed to start")
            if stderr:
                print(stderr.decode())
            return None
        
        print(f"✅ Server started successfully!")
        return process
    
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return None


def check_server_health():
    """Check if server is responding."""
    try:
        import urllib.request
        import json
        
        req = urllib.request.Request(f"{SERVER_URL}/health")
        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read().decode())
            return data.get('status') == 'ok'
    except:
        return False


def open_browser(project_root):
    """Open the web UI in the default browser."""
    web_ui_file = project_root / WEB_UI_PATH
    
    if not web_ui_file.exists():
        print(f"❌ Error: Web UI not found at {web_ui_file}")
        return False
    
    # Convert to file:// URL
    file_url = web_ui_file.as_uri()
    
    print(f"🌐 Opening web interface...")
    try:
        webbrowser.open(file_url)
        print(f"✅ Browser opened!")
        return True
    except Exception as e:
        print(f"❌ Failed to open browser: {e}")
        print(f"Please open manually: {file_url}")
        return False


def print_banner():
    """Print welcome banner."""
    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║                    🗺️  MAPTOPOSTER  🗺️                     ║
║                                                            ║
║              Create Beautiful Map Posters                  ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
""")


def print_instructions(server_url, web_ui_path):
    """Print usage instructions."""
    print(f"""
┌─────────────────────────────────────────────────────────────┐
│  🎉 Maptoposter is now running!                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Server:  {server_url:<45}  │
│  Web UI:  Opened in your browser                           │
│                                                             │
│  💡 Tips:                                                   │
│    • Use small cities (Monaco, Vaduz) for quick tests      │
│    • Generation takes 3-5 minutes for large cities         │
│    • Watch the progress timer during generation            │
│                                                             │
│  🛑 To stop: Press Ctrl+C in this terminal                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
""")


def main():
    """Main launcher function."""
    print_banner()
    
    project_root = get_project_root()
    
    # Check dependencies
    if not check_dependencies():
        print("⚠️  Required dependencies not found")
        if not install_dependencies():
            sys.exit(1)
    
    # Start server
    server_process = start_server(project_root)
    if not server_process:
        sys.exit(1)
    
    # Wait for server to be ready
    print("⏳ Waiting for server to be ready...")
    for _ in range(10):
        if check_server_health():
            break
        time.sleep(0.5)
    else:
        print("⚠️  Server health check failed, but continuing anyway...")
    
    # Open browser
    open_browser(project_root)
    
    # Print instructions
    print_instructions(SERVER_URL, WEB_UI_PATH)
    
    # Keep running and wait for Ctrl+C
    try:
        server_process.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
        print("✅ Server stopped. Goodbye!")


if __name__ == "__main__":
    main()
