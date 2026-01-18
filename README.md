# City Map Poster Generator (Interactive Edition)

**Create beautiful, minimalist map posters for any city in the world.** 

<img src="posters/vancouver_forest_20260118_203925.png" width="400">
<img src="posters/norfolk_midnight_blue_20260118_202715.png" width="400">
<img src="posters/tokyo_neon_cyberpunk_20260118_200857.png" width="400">
<img src="posters/oxford_warm_beige_20260118_200421.png" width="400">

## 🚀 New Features
This fork introduces `create_interactive_map_poster.py`, a powerful engine that allows you to:
1.  **Visualize Buildings:** Automatically downloads and renders buildings in a subtle "blueprint" style (`z-index` optimized).
2.  **Interactive Highlighting:** Highlight specific city features (Universities, Military Zones, Hospitals) without writing code.
3.  **Smart Layering:** Highlights are drawn with a faded fill *under* buildings and a strong contour *over* roads.

---

## Installation

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/maptoposter.git
cd maptoposter

# Install dependencies (Requires Python 3.10+)
pip install -r requirements.txt
```

### How it works
The script will pause and ask:
1.  **How many highlights?** (e.g., 2)
2.  **Key & Value?** (Enter OpenStreetMap tags)
3.  **Color?** (Enter a Hex code)

#### 🧪 Interactive "Recipes" to try:

| Style | City | Theme | Interactive Inputs (When prompted) |
| :--- | :--- | :--- | :--- |
| **Academic** | Oxford, UK | `warm_beige` | **1.** `amenity`=`university` (Red)<br>**2.** `amenity`=`library` (Gold) |
| **Tactical** | Norfolk, USA | `midnight_blue` | **1.** `landuse`=`military` (#FF4500)<br>**2.** `man_made`=`pier` (Cyan) |
| **Nature** | Vancouver, CA | `forest` | **1.** `natural`=`wood` (ForestGreen)<br>**2.** `leisure`=`park` (LightGreen) |
| **Medical** | Houston, USA | `blueprint` | **1.** `amenity`=`hospital` (White)<br>**2.** `building`=`medical` (Red) |
| **Heritage** | Kyoto, JP | `japanese_ink` | **1.** `historic`=`temple` (Orange)<br>**2.** `tourism`=`attraction` (Gold) |
