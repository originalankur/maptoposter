# MapPoster Studio

A premium GUI for generating aesthetic map posters.

## Requirements

- Python 3.8+
- Internet connection (for fetching map data)

## Setup

1. **Create a virtual environment:**
   ```powershell
   python -m venv venv
   ```

2. **Activate the environment:**
   ```powershell
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

## Running the App

Run the application from the `MapPosterStudio` directory:

```powershell
cd MapPosterStudio
python app.py
```

## Features

- **Interactive Preview:** Quickly check how your map looks before exporting.
- **Customizable:** Adjust city, theme, distance, and text.
- **High Res Export:** Export posters up to 600 DPI.
- **Themes:** Supports all themes available in the `themes/` directory.

## Building an Executable (.exe)

To bundle the application as a standalone executable using PyInstaller:

1. Install PyInstaller:
   ```powershell
   pip install pyinstaller
   ```

2. Run the build command (from the `MapPosterStudio` directory):

   ```powershell
   pyinstaller --noconfirm --onedir --windowed --name "MapPoster Studio" --add-data "poster_engine;poster_engine" --add-data "ui;ui" --icon "assets/icon.png" app.py
   ```

   *Note: You may need to manually copy the `themes`, `fonts`, and `create_map_poster.py` to the output `dist/MapPoster Studio` directory or adjust the spec file to include them, as the external script is outside the main module package.*
