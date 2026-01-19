import os
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Rectangle, Circle, Polygon as MplPolygon
from matplotlib.collections import LineCollection
from shapely.geometry import Point, Polygon, LineString, MultiPolygon
import geopandas as gpd
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, List, Union
from pathlib import Path

# Try importing qrcode, but don't fail if missing
try:
    import qrcode
except ImportError:
    qrcode = None

@dataclass
class StylePreset:
    name: str
    bg_color: str
    text_color: str
    water_color: str
    parks_color: str
    road_colors: Dict[str, str]
    road_widths: Dict[str, float]
    road_alphas: Dict[str, float] = field(default_factory=lambda: {"major": 1.0, "minor": 1.0, "path": 0.8})
    accent_color: str = "#FFD700"
    texture_type: str = "subtle"  # off, subtle, paper, grain
    vignette_strength: str = "subtle" # off, subtle, medium
    linework_style: str = "layered" # flat, layered
    font_weights: Dict[str, str] = field(default_factory=lambda: {"title": "bold", "subtitle": "light", "coords": "regular"})

# --- 1. PRESETS DEFINITION ---

PRESETS = {
    "classic_bw": StylePreset(
        name="classic_bw",
        bg_color="#FFFFFF",
        text_color="#000000",
        water_color="#E0E0E0",
        parks_color="#F0F0F0",
        road_colors={"major": "#000000", "minor": "#333333", "path": "#666666"},
        road_widths={"major": 1.5, "minor": 0.8, "path": 0.5},
        texture_type="off",
        vignette_strength="off",
        linework_style="flat"
    ),
    "blueprint": StylePreset(
        name="blueprint",
        bg_color="#003366", # Deep blue
        text_color="#FFFFFF",
        water_color="#004080",
        parks_color="#002244", # Darker blue
        road_colors={"major": "#FFFFFF", "minor": "#AACCFF", "path": "#5577AA"},
        road_widths={"major": 1.2, "minor": 0.6, "path": 0.3},
        road_alphas={"major": 0.9, "minor": 0.7, "path": 0.5},
        accent_color="#00FFFF",
        texture_type="subtle", # mild grid effect ideally, but subtle noise works
        vignette_strength="subtle",
        linework_style="flat"
    ),
    "noir": StylePreset(
        name="noir",
        bg_color="#121212",
        text_color="#E0E0E0",
        water_color="#1A1A1A",
        parks_color="#0A0A0A",
        road_colors={"major": "#D0D0D0", "minor": "#808080", "path": "#404040"},
        road_widths={"major": 1.4, "minor": 0.7, "path": 0.4},
        road_alphas={"major": 0.95, "minor": 0.8, "path": 0.6},
        texture_type="grain",
        vignette_strength="medium",
        linework_style="layered"
    ),
    "vintage": StylePreset(
        name="vintage",
        bg_color="#FDF6E3", # Warm paper
        text_color="#586E75", # Muted dark teal/grey
        water_color="#D8E8E8", # Pale blue-ish
        parks_color="#E8E8D8", # Pale sage
        road_colors={"major": "#8B7355", "minor": "#A69580", "path": "#C0B2A0"}, # Sepia tones
        road_widths={"major": 1.3, "minor": 0.7, "path": 0.4},
        texture_type="paper",
        vignette_strength="subtle",
        linework_style="flat",
        font_weights={"title": "regular", "subtitle": "light", "coords": "light"}
    ),
    "nchs_premium": StylePreset(
        name="nchs_premium",
        bg_color="#0B2C5D", # NCHS Blue
        text_color="#FFFFFF",
        water_color="#1A3A6D",
        parks_color="#082045",
        road_colors={"major": "#FFFFFF", "minor": "#A0B0C0", "path": "#506070"},
        road_widths={"major": 1.4, "minor": 0.6, "path": 0.3},
        road_alphas={"major": 1.0, "minor": 0.7, "path": 0.4},
        accent_color="#C5B358", # Vegas Gold / Muted Gold
        texture_type="subtle",
        vignette_strength="subtle",
        linework_style="layered"
    )
}

def build_style(preset_name: str, overrides: Dict = None) -> StylePreset:
    """Load a preset and apply optional overrides."""
    base = PRESETS.get(preset_name, PRESETS["classic_bw"])
    
    # We should return a copy or new instance to avoid mutating the global PRESETS
    # For simplicity, let's create a new instance with the same values
    style = StylePreset(
        name=base.name,
        bg_color=base.bg_color,
        text_color=base.text_color,
        water_color=base.water_color,
        parks_color=base.parks_color,
        road_colors=base.road_colors.copy(),
        road_widths=base.road_widths.copy(),
        road_alphas=base.road_alphas.copy(),
        accent_color=base.accent_color,
        texture_type=base.texture_type,
        vignette_strength=base.vignette_strength,
        linework_style=base.linework_style,
        font_weights=base.font_weights.copy()
    )

    if overrides:
        if "accent" in overrides and overrides["accent"]:
            style.accent_color = overrides["accent"]
        if "texture" in overrides and overrides["texture"]:
            style.texture_type = overrides["texture"]
        if "vignette" in overrides and overrides["vignette"]:
            style.vignette_strength = overrides["vignette"]
        if "linework" in overrides and overrides["linework"]:
            style.linework_style = overrides["linework"]
            
    return style

# --- 2. UTILITIES ---

def parse_bbox(bbox_str: str) -> Tuple[float, float, float, float]:
    """Parse 'north,south,east,west' string to floats."""
    try:
        parts = [float(x.strip()) for x in bbox_str.split(",")]
        if len(parts) != 4:
            raise ValueError
        return tuple(parts)
    except ValueError:
        raise ValueError("bbox must be 'north,south,east,west' floats")

def parse_format_preset(name: str) -> Tuple[float, float]:
    """Return width, height in inches."""
    presets = {
        "preview": (12, 16), # Keeping original default ratio roughly
        "18x24": (18, 24),
        "24x36": (24, 36),
        "a3": (11.7, 16.5),
        "a2": (16.5, 23.4)
    }
    return presets.get(name, (12, 16))

def parse_hex_color(s: str) -> str:
    """Validate and return hex color."""
    if not s.startswith("#"):
        s = "#" + s
    if not len(s) in (4, 7):
        raise ValueError(f"Invalid hex color: {s}")
    return s

# --- 3. GEOMETRY PROCESSING ---

def simplify_roads(edges_gdf: gpd.GeoDataFrame, detail: str = "standard", hide_flags: Dict = None) -> gpd.GeoDataFrame:
    """Filter roads based on detail level and flags."""
    if edges_gdf is None or edges_gdf.empty:
        return edges_gdf
        
    df = edges_gdf.copy()
    hide_flags = hide_flags or {}
    
    # Base filter by highway tag existence
    if 'highway' not in df.columns:
        return df

    # Normalize highway to string (sometimes it's a list)
    def get_highway_type(x):
        if isinstance(x, list):
            return x[0]
        return str(x)
        
    df['highway_type'] = df['highway'].apply(get_highway_type)
    
    # Get service attribute (for parking_aisle detection)
    def get_service_type(x):
        if x is None or (isinstance(x, float) and np.isnan(x)):
            return None
        if isinstance(x, list):
            return str(x[0]) if x else None
        return str(x)
    
    if 'service' in df.columns:
        df['service_type'] = df['service'].apply(get_service_type)
    else:
        df['service_type'] = None
    
    # Exclude logic
    exclude_types = set()
    
    if hide_flags.get("hide_parking"):
        exclude_types.update(["service", "parking_aisle"]) # simplistic
        # Better: check 'service' tag if exists
        
    if hide_flags.get("hide_service"):
        exclude_types.add("service")
        
    if hide_flags.get("hide_footpaths"):
        exclude_types.update(["footway", "path", "cycleway", "steps", "pedestrian"])

    # Detail levels
    keep_core = {"primary", "secondary", "tertiary", "residential", "unclassified", "living_street", "service", "road"}
    drop_paths = {"footway", "path", "pedestrian", "steps", "cycleway", "track"}
    
    def road_keep(row, detail):
        """Determine if a road should be kept based on detail level."""
        hwy = row.get("highway_type")
        svc = row.get("service_type")
        
        if detail == "campus":
            # Drop foot/cycle paths (unless max detail)
            if hwy in drop_paths:
                return False
            # Drop parking aisles but keep other service roads
            if hwy == "service" and svc == "parking_aisle":
                return False
            # Keep core road types
            return hwy in keep_core
        elif detail == "max":
            # Include everything, minimal filtering (only explicit hides)
            return True
        else:  # standard
            # Standard filtering (existing behavior)
            return True

    # Apply filtering
    # 1. remove explicit hides
    mask = ~df['highway_type'].isin(exclude_types)
    
    # 2. specific detail logic
    if detail == "campus":
        # Apply campus-specific filtering
        campus_mask = df.apply(lambda row: road_keep(row, detail), axis=1)
        mask = mask & campus_mask
    elif detail == "max":
        # Max detail: only apply explicit hides
        pass
    else:  # standard
        # Standard detail: apply explicit hides only
        pass
        
    return df[mask]

def collapse_tiers(edges_gdf: gpd.GeoDataFrame, tiers: str = "simple") -> gpd.GeoDataFrame:
    """Assign a 'tier' column: major, minor, path."""
    if edges_gdf is None or edges_gdf.empty:
        return edges_gdf
    
    df = edges_gdf.copy()
    
    major_types = {'motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary', 'primary_link', 'secondary', 'secondary_link'}
    path_types = {'footway', 'path', 'cycleway', 'steps', 'pedestrian', 'track'}
    # All else is minor (tertiary, residential, unclassified, service)

    def get_tier(hw):
        if isinstance(hw, list):
            hw = hw[0]
        hw = str(hw)
        if hw in major_types:
            return "major"
        if hw in path_types:
            return "path"
        return "minor"
        
    df['tier'] = df['highway'].apply(get_tier)
    return df

# --- 4. RENDERING PIPELINE ---

def add_texture_overlay(ax, strength="subtle", seed=42):
    """Add noise texture to the axes."""
    if strength == "off":
        return
        
    # Generate noise image
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    
    # We'll use a fixed size noise grid stretched over the view
    # This prevents vector bloat.
    # ideally we want resolution independent, but matplotlib imshow is raster.
    w, h = 2000, 2000 
    np.random.seed(seed)
    
    if strength == "grain":
        noise = np.random.normal(0, 1, (h, w))
        alpha = 0.05
        cmap = "gray"
    elif strength == "paper":
        # Simulating paper with some low freq noise + high freq
        noise = np.random.normal(0, 1, (h, w))
        alpha = 0.03
        cmap = mcolors.LinearSegmentedColormap.from_list("paper", ["#FDF6E3", "#8B7355"])
    else: # subtle
        noise = np.random.normal(0, 1, (h, w))
        alpha = 0.03
        cmap = "gray"

    ax.imshow(noise, extent=[xlim[0], xlim[1], ylim[0], ylim[1]], 
              cmap=cmap, alpha=alpha, zorder=90, aspect='auto')

def add_vignette(ax, strength="subtle"):
    """Add radial vignette."""
    if strength == "off":
        return
        
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    
    x = np.linspace(-1, 1, 100)
    y = np.linspace(-1, 1, 100)
    X, Y = np.meshgrid(x, y)
    R = np.sqrt(X**2 + Y**2)
    
    # Vignette intensity
    if strength == "medium":
        # darker corners
        alpha_map = np.clip((R - 0.5) * 0.8, 0, 1)
    else: # subtle
        alpha_map = np.clip((R - 0.7) * 0.5, 0, 1)
        
    # Create black overlay with varying alpha
    z = np.zeros((*alpha_map.shape, 4))
    z[:,:,3] = alpha_map # Alpha channel
    
    ax.imshow(z, extent=[xlim[0], xlim[1], ylim[0], ylim[1]], 
              zorder=95, aspect='auto', interpolation='bicubic')

def render_poster(bundle: Dict, output_path: str, format_type: str = "png"):
    """
    Main rendering function.
    bundle contains:
        - edges: gpd.GeoDataFrame (projected)
        - water: gpd.GeoDataFrame or None
        - parks: gpd.GeoDataFrame or None
        - campus_poly: Polygon or None
        - style: StylePreset
        - bbox: (xmin, ymin, xmax, ymax) projected bounds
        - labels: dict(label1, label2, label3, signature)
        - config: dict(size_inches, dpi, show_scale, show_north, etc.)
    """
    style = bundle["style"]
    config = bundle["config"]
    bbox = bundle["bbox"] # projected coords: minx, miny, maxx, maxy
    
    # 1. Setup Figure
    w_in, h_in = config.get("size_inches", (12, 16))
    dpi = config.get("dpi", 300)
    
    fig, ax = plt.subplots(figsize=(w_in, h_in), dpi=dpi)
    fig.patch.set_facecolor(style.bg_color)
    ax.set_facecolor(style.bg_color)
    
    # Set extent
    if bbox is not None:
        ax.set_xlim(bbox[0], bbox[2])
        ax.set_ylim(bbox[1], bbox[3])
    
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    # 2. Draw Background Layers (Water, Parks)
    if bundle.get("water") is not None and not bundle["water"].empty:
        bundle["water"].plot(ax=ax, facecolor=style.water_color, edgecolor='none', zorder=1)
        
    if bundle.get("parks") is not None and not bundle["parks"].empty:
        bundle["parks"].plot(ax=ax, facecolor=style.parks_color, edgecolor='none', zorder=2)
        
    # 3. Draw Campus Highlight (Underlay or Overlay?)
    # If we want a glow, maybe under roads but over ground
    campus_poly = bundle.get("campus_poly")
    if campus_poly:
        # Convert shapely geom to matplotlib patch
        # But simpler to use gpd if we wrap it
        gpd.GeoSeries([campus_poly]).plot(ax=ax, facecolor="none", edgecolor=style.accent_color, linewidth=2, alpha=0.6, zorder=5)
        # Glow effect (simulated with wider stroke)
        gpd.GeoSeries([campus_poly]).plot(ax=ax, facecolor="none", edgecolor=style.accent_color, linewidth=6, alpha=0.2, zorder=4.9)

    # 4. Draw Roads
    edges = bundle["edges"]
    if edges is not None and not edges.empty:
        # Sort by tier so major roads are on top? Or path on top?
        # Usually: path < minor < major for map clarity, or major < minor < path for campus?
        # Standard map: minor, then major.
        
        # Get detail and tiers mode from config
        config = bundle.get("config", {})
        detail = config.get("detail", "standard")
        tiers_mode = config.get("tiers", "simple")
        
        # Split by tier
        tiers = ["path", "minor", "major"]
        for tier in tiers:
            subset = edges[edges["tier"] == tier]
            if subset.empty:
                continue
            
            color = style.road_colors.get(tier, "#000000")
            width = style.road_widths.get(tier, 1.0)
            alpha = style.road_alphas.get(tier, 1.0)
            
            # Ensure minor roads are visible in campus mode with simple tiers
            if tier == "minor" and tiers_mode == "simple" and detail == "campus":
                # Ensure minimum visibility for minor roads
                if width < 0.5:
                    width = 0.5
                if alpha < 0.6:
                    alpha = 0.6
            
            # Layered mode: draw casing
            if style.linework_style == "layered":
                # Casing is wider and darker/lighter
                casing_width = width + 1.2
                casing_alpha = alpha * 0.5
                # For casing, if road is light, casing is dark, and vice versa?
                # Or just use BG color to create separation?
                # Often casing is slightly darker than bg to create "imprint" or "lift"
                # Let's try drawing with bg color as casing to create gaps at intersections if using alpha?
                # Actually, standard "casing" is usually a border. 
                # Let's keep it simple: just draw the line.
                
                # If "layered", maybe we draw the road twice?
                # One thick pass, one thin pass?
                # Pass 1: Glow/Shadow
                subset.plot(ax=ax, color=style.accent_color if tier == "major" and style.name == "nchs_premium" else color, 
                           linewidth=width+1, alpha=0.3*alpha, zorder=10)
                # Pass 2: Core
                subset.plot(ax=ax, color=color, linewidth=width, alpha=alpha, zorder=11)
            else:
                subset.plot(ax=ax, color=color, linewidth=width, alpha=alpha, zorder=10)

    # 5. Highlights (Point)
    highlight_point = bundle.get("highlight_point") # (x, y) projected
    if highlight_point:
        px, py = highlight_point
        # Draw a ring
        circle = Circle((px, py), radius=150, fill=False, edgecolor=style.accent_color, linewidth=2, zorder=20)
        ax.add_patch(circle)
        # Inner dot
        circle_inner = Circle((px, py), radius=30, fill=True, color=style.accent_color, zorder=20)
        ax.add_patch(circle_inner)

    # 6. Typography
    # We use matplotlib text for vector output support (unlike PIL in original)
    # Positioning is tricky in matplotlib relative to axes.
    # We'll use axis-relative coordinates (0-1).
    
    lbl_cfg = bundle.get("labels", {})
    l1 = lbl_cfg.get("label1")
    l2 = lbl_cfg.get("label2")
    l3 = lbl_cfg.get("label3")
    
    # We can use the font manager from main, or load by path.
    # Simplified here: use system fonts or provided paths if we had them passed in bundle.
    # For now, default sans-serif.
    
    text_y_base = 0.12
    spacing = 0.04
    
    if l1:
        font_weight = style.font_weights.get("title", "bold")
        ax.text(0.5, text_y_base, l1.upper(), transform=ax.transAxes, 
                ha='center', va='bottom', color=style.text_color, 
                fontsize=24, fontweight=font_weight, zorder=30, fontname="DejaVu Sans")
    
    if l2:
        font_weight = style.font_weights.get("subtitle", "light")
        # Letter spacing simulation is hard in pure mpl without tweaking.
        # Just standard text for now.
        ax.text(0.5, text_y_base - spacing, l2.upper(), transform=ax.transAxes,
                ha='center', va='bottom', color=style.text_color,
                fontsize=14, fontweight=font_weight, alpha=0.9, zorder=30, fontname="DejaVu Sans")
        
    if l3:
        font_weight = style.font_weights.get("coords", "regular")
        ax.text(0.5, text_y_base - 2*spacing, l3, transform=ax.transAxes,
                ha='center', va='bottom', color=style.text_color,
                fontsize=10, fontweight=font_weight, alpha=0.7, zorder=30, fontname="DejaVu Sans")

    # 7. Extras: Scale Bar, North Arrow, Signature
    if config.get("show_north_arrow"):
        # Simple N arrow at top right
        ax.text(0.95, 0.95, "N", transform=ax.transAxes, ha='center', va='bottom',
                color=style.text_color, fontsize=12, fontweight='bold', zorder=30)
        # Draw arrow below N
        arrow_x = 0.95
        arrow_y = 0.93
        ax.arrow(arrow_x, arrow_y, 0, 0.02, transform=ax.transAxes, 
                 color=style.text_color, width=0.002, head_width=0.01, zorder=30)

    # 8. Effects (Raster Overlays)
    add_texture_overlay(ax, style.texture_type)
    add_vignette(ax, style.vignette_strength)

    # 9. QR Code
    qr_url = bundle.get("qr_url")
    if qr_url and qrcode:
        # Generate QR
        qr = qrcode.QRCode(box_size=10, border=1)
        qr.add_data(qr_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color=style.text_color, back_color=style.bg_color)
        
        # Convert to array and place
        # This is raster, but fine for QR
        qr_arr = np.array(qr_img.convert("RGBA"))
        
        # Place in corner (bottom right or left)
        # Matplotlib inset axes
        from mpl_toolkits.axes_grid1.inset_locator import inset_axes
        axins = inset_axes(ax, width="10%", height="10%", loc='lower right', borderpad=2)
        axins.imshow(qr_arr)
        axins.axis('off')
        
        if bundle.get("qr_label"):
            ax.text(0.98, 0.12, bundle["qr_label"], transform=ax.transAxes,
                   ha='right', va='bottom', color=style.text_color, fontsize=6, zorder=30)

    # 10. Save
    print(f"Saving poster to {output_path}...")
    plt.savefig(output_path, dpi=dpi, facecolor=style.bg_color, bbox_inches=None) # bbox_inches='tight' might cut margin
    plt.close(fig)
