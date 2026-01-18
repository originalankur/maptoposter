# 🚀 Quick Start Guide

Get Maptoposter running in **30 seconds** on any operating system!

## One-Time Setup (5 minutes)

### 1. Install Python Dependencies

```bash
# Navigate to the maptoposter directory
cd maptoposter

# Install all required packages
pip install -r requirements.txt
```

That's it for setup! Now you can run Maptoposter anytime.

---

## 🎯 Launch Maptoposter

Choose your operating system:

### 🍎 macOS
**Option A: Double-click** *(easiest)*
1. Navigate to `universal-ui/` folder in Finder
2. Double-click `launcher.command`
3. Browser opens automatically!

**Option B: Terminal**
```bash
cd universal-ui
./launcher.command
```

### 🪟 Windows
**Option A: Double-click** *(easiest)*
1. Navigate to `universal-ui\` folder in File Explorer
2. Double-click `launcher.bat`
3. Browser opens automatically!

**Option B: Command Prompt**
```cmd
cd universal-ui
launcher.bat
```

### 🐧 Linux
**Option A: Double-click** *(if file manager supports)*
1. Navigate to `universal-ui/` folder
2. Double-click `launcher.sh` (or `launcher.command`)
3. Browser opens automatically!

**Option B: Terminal**
```bash
cd universal-ui
./launcher.sh
```

### 🐍 Any OS (Python)
```bash
cd universal-ui
python3 launcher.py
```

---

## ✨ What Happens When You Launch?

1. ✅ Auto-installs Flask dependencies (if missing)
2. 🚀 Starts local server on port 8001
3. 🌐 Opens web interface in your default browser
4. 🎨 Ready to create map posters!

You'll see:
```
╔════════════════════════════════════════════════════════════╗
║                    🗺️  MAPTOPOSTER  🗺️                     ║
║              Create Beautiful Map Posters                  ║
╚════════════════════════════════════════════════════════════╝

📦 Checking dependencies...
✅ Dependencies installed successfully!
🚀 Starting server on http://127.0.0.1:8001...
✅ Server started successfully!
🌐 Opening web interface...
✅ Browser opened!

┌─────────────────────────────────────────────────────────────┐
│  🎉 Maptoposter is now running!                             │
│                                                             │
│  Server:  http://127.0.0.1:8001                             │
│  Web UI:  Opened in your browser                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎨 Create Your First Poster

In the web interface:

1. **Enter a city**: Start small for faster results
   - Quick test: `Monaco` or `Vaduz`
   - Medium: `Berlin` or `Amsterdam`
   - Large: `Paris` or `Tokyo` (takes 5-8 minutes)

2. **Choose a theme**: 17 beautiful themes available
   - `noir` - Classic black & white
   - `ocean` - Calming blues
   - `neon_cyberpunk` - Vibrant colors

3. **Set radius**: 1500-5000 meters

4. **Click Generate**: Watch the progress timer!

⏱️ **Generation time:**
- Small cities: 1-2 minutes
- Medium cities: 3-5 minutes
- Large cities: 5-8 minutes

---

## 🛑 Stop Maptoposter

Press `Ctrl+C` in the terminal window where the launcher is running.

---

## 🆘 Troubleshooting

### "Command not found" or "python3 not found"
- Make sure Python 3.6+ is installed: `python3 --version`
- Windows users: Try `python` instead of `python3`

### "Module not found" errors
```bash
cd maptoposter
pip install -r requirements.txt
```

### Port 8001 already in use
Edit `launcher.py` and change `SERVER_PORT = 8001` to another port (e.g., 8002)

### Browser doesn't open automatically
Manually open: `universal-ui/web/index.html` in your browser

### Generation takes too long
- Try smaller cities first (Monaco, Vaduz)
- Use smaller radius (1500m instead of 5000m)
- Be patient - large cities need 5-8 minutes

---

## 📦 Distribution

Want to share Maptoposter with others?

### Simple Distribution
1. Zip the entire `maptoposter` folder
2. Recipients just need Python 3.6+ installed
3. They run the launcher and dependencies auto-install!

### Desktop App (Advanced)
Build native apps for Windows/macOS/Linux using Tauri:

```bash
cd universal-ui/tauri
npm install
npm run tauri build
```

See [PACKAGING.md](PACKAGING.md) for details.

---

## 🎉 You're Ready!

That's it! You now have a fully functional map poster generator that:
- ✅ Works on any OS (Windows, macOS, Linux)
- ✅ Auto-installs dependencies
- ✅ Opens browser automatically
- ✅ Provides real-time progress feedback
- ✅ Can be distributed to non-technical users

**Enjoy creating beautiful map posters! 🗺️✨**
