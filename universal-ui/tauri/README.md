# Tauri Scaffold for Maptoposter (Dual Mode)

This directory contains a Tauri project scaffold demonstrating how the web UI could be packaged as a native desktop application with automatic server startup.

## ⚠️ Status: Configuration Scaffold

This is **not a complete, buildable Tauri application** yet. It's a configuration skeleton showing how maptoposter could be distributed as a native app with integrated server management.

## What's Included

- `tauri.conf.json` - Tauri configuration with server integration
- `Cargo.toml` - Rust dependencies
- `build.rs` - Build script
- `src/main.rs` - Main Rust entry point with server management

## Key Features (When Complete)

1. **Automatic Server Launch**: Starts `run_local.py --serve` on app startup
2. **Native Window**: Wraps the web UI in a native application window
3. **Background Server**: Manages the Python server process
4. **Cross-Platform**: Supports macOS, Windows, and Linux

## How It Would Work

```
App Launch → Start Python Server → Load Web UI → One-Click Generation
```

The desktop app would:
1. Launch the Python HTTP server in the background
2. Wait for server to be ready
3. Open the web UI in a native window
4. Allow seamless poster generation
5. Clean up server process on app exit

## Building (Future)

When this becomes production-ready:

```bash
# Install Tauri CLI
cargo install tauri-cli

# Install dependencies
cd universal-ui/tauri
cargo fetch

# Build the app
cargo tauri build

# Development mode
cargo tauri dev
```

## Current Recommendation

For now, **use the web interface** with manual server startup:

```bash
# Terminal 1: Start server
python universal-ui/runner/run_local.py --serve

# Terminal 2 (or browser): Open UI
open universal-ui/web/index.html
```

## Future Enhancements

- [ ] Bundle Python runtime with app
- [ ] Auto-install Python dependencies
- [ ] Native file picker for poster loading
- [ ] System tray integration
- [ ] Auto-update functionality
- [ ] Native notifications

## Learn More

- [Tauri Documentation](https://tauri.app)
- [Tauri Sidecar Pattern](https://tauri.app/v1/guides/building/sidecar)
- [Managing Background Processes](https://tauri.app/v1/api/js/shell)
