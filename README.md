# MapPoster Studio 🌍📍

A premium, python-based tool for generating aesthetic, high-resolution map posters of any city in the world. Now featuring a fully functional **GUI Studio**.

![MapPoster Studio Preview](assets/preview_placeholder.png) 
*(Note: Add a screenshot of the app here)*

## ✨ Features

### 🖥️ MapPoster Studio (New GUI)
A modern, dark-themed desktop application built with **PySide6** (Qt).
*   **Studio Layout**: Professional split-view interface with a collapsible settings panel and a large real-time preview area.
*   **Interactive Preview**: Zoom controls (Fit, 50%, 100%) to inspect details before exporting.
*   **Customization**:
    *   **Location**: Easy city and country input.
    *   **Visual Styles**: Choose from presets (Noir, Blueprint, Cyberpunk, etc.) or manually select from 15+ themes.
    *   **Map Control**: Adjust the map radius (zoom level) from 500m to 50km.
    *   **Typography**: Custom Title, Subtitle, and Tagline support with auto-uppercase options.
*   **High-Res Export**: Export PNGs at custom DPI (up to 600 DPI) for print-ready quality.
*   **Theme Aware**: The application itself sports a sleek dark mode.

### 💻 CLI Script (`create_map_poster.py`)
The powerful engine powering the studio, available for batch processing or terminal lovers.
*   `--city`, `--country`: Specify location.
*   `--theme`: Choose aesthetic (e.g., `noir`, `midnight_blue`, `sunset`).
*   `--dpi`: Set output resolution.
*   `--distance`: Set map radius in meters.

## 🚀 Getting Started

### Prerequisites
*   Python 3.8+
*   Internet connection (to fetch OpenStreetMap data)

### Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/Harsha754-ml/maptoposter.git
    cd maptoposter
    ```

2.  **Create a Virtual Environment** (Recommended)
    ```powershell
    python -m venv venv
    .\venv\Scripts\Activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r MapPosterStudio/requirements.txt
    ```

### ▶️ Running the App

To launch the **MapPoster Studio** GUI:

```bash
cd MapPosterStudio
python app.py
```

To use the **CLI** directly:

```bash
python create_map_poster.py --city "New York" --country "USA" --theme noir --dpi 300
```

## 🎨 Available Themes
*   **Noir**: High contrast black & white.
*   **Blueprint**: Technical architectural style.
*   **Midnight Blue**: Deep blue aesthetic.
*   **Neon Cyberpunk**: Futuristic glowing colors.
*   **Sunset**: Warm gradients.
*   ...and many more in the `themes/` folder.

## 📦 Building Standalone (.exe)
You can bundle the app into a single executable file using PyInstaller:

```powershell
cd MapPosterStudio
pyinstaller --noconfirm --onedir --windowed --name "MapPoster Studio" --add-data "poster_engine;poster_engine" --add-data "ui;ui" --icon "assets/icon.png" app.py
```

## 📄 License
MIT License