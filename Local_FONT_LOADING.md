# Font Loading Guide

This document explains how to use custom fonts with the City Map Poster Generator.

## Overview

The application supports three methods for loading fonts, in priority order:

1. **Google Fonts** (`--font-family`) - Highest priority
2. **Local Font Path** (`--font-path`) - Second priority  
3. **Default Roboto** - Automatic fallback

## Using Local Fonts

### Single Font File

Load a specific font file for all text weights (bold, regular, light):

```bash
python create_map_poster.py -c "Paris" -C "France" --font-path "path/to/font.ttf"
```

Examples:
```bash
# Windows absolute path
python create_map_poster.py -c "Paris" -C "France" --font-path "D:\Fonts\CustomFont.ttf"

# Unix absolute path
python create_map_poster.py -c "Tokyo" -C "Japan" --font-path "/usr/share/fonts/truetype/myfont.ttf"

# Relative path
python create_map_poster.py -c "Berlin" -C "Germany" --font-path "./fonts/custom.ttf"
```

### Font Directory

Load multiple font files from a directory. The function intelligently detects font weights:

```bash
python create_map_poster.py -c "Barcelona" -C "Spain" --font-path "path/to/fonts/"
```

The function looks for the following patterns (case-insensitive):

**Bold weight patterns:**
- `*bold*` (e.g., `font-bold.ttf`, `Font_Bold.otf`)
- `*700*` (e.g., `font-700.ttf`)

**Regular weight patterns:**
- `*regular*` (e.g., `font-regular.ttf`)
- `*400*` (e.g., `font-400.ttf`)
- `*normal*` (e.g., `font-normal.ttf`)

**Light weight patterns:**
- `*light*` (e.g., `font-light.ttf`)
- `*300*` (e.g., `font-300.ttf`)
- `*thin*` (e.g., `font-thin.ttf`)

**Example directory structure:**
```
fonts/
├── myfont-bold.ttf
├── myfont-regular.ttf
├── myfont-light.ttf
└── alternate-300.otf
```

Then use:
```bash
python create_map_poster.py -c "Rome" -C "Italy" --font-path "fonts/"
```

### Path Handling

The function handles paths robustly:

- **Absolute paths**: `/path/to/font.ttf` or `C:\path\to\font.ttf`
- **Relative paths**: `./fonts/myfont.ttf` or `fonts/myfont.ttf`
- **Home directory expansion**: `~/fonts/myfont.ttf` (expands to user home)
- **Windows & Unix paths**: Automatically handled regardless of OS
- **Spaces in paths**: Fully supported with proper escaping

## Using Google Fonts

Download fonts directly from Google Fonts:

```bash
python create_map_poster.py -c "Berlin" -C "Germany" --font-family "Noto Sans JP"
python create_map_poster.py -c "Bangkok" -C "Thailand" --font-family "Noto Sans Thai"
```

Supports any family available on [Google Fonts](https://fonts.google.com/)

## Supported Font Formats

- `.ttf` - TrueType Font
- `.otf` - OpenType Font
- `.woff` - Web Open Font Format
- `.woff2` - Web Open Font Format 2 (compressed)

## Examples

### Using a custom display font

```bash
python create_map_poster.py \
  -c "Tokyo" \
  -C "Japan" \
  -t japanese_ink \
  --font-path "C:\MyFonts\NotoSansJP-Bold.ttf" \
  -d 15000
```

### Using a font directory with multiple weights

```bash
python create_map_poster.py \
  -c "Paris" \
  -C "France" \
  -t pastel_dream \
  --font-path "./custom_fonts/" \
  -d 10000
```

### Combining with other options

```bash
python create_map_poster.py \
  -c "Barcelona" \
  -C "Spain" \
  --font-path "/usr/share/fonts/custom/" \
  -t warm_beige \
  -W 14 \
  -H 18 \
  --display-city "Barcelona" \
  --display-country "España"
```

## Fallback Behavior

If font loading fails at any stage:

1. If `--font-family` is provided but fails → tries `--font-path` (if provided)
2. If `--font-path` is provided but fails → uses default Roboto
3. If both fail → uses default Roboto fonts

The console will show appropriate warning messages about what fallback was used.

## Troubleshooting

### "Font path does not exist"
- Check that the path is correct and file/directory exists
- Use absolute paths if relative paths don't work
- On Windows, use `\` or `\\` for path separators (or use forward slashes `/`)

### "Unsupported font format"
- Only `.ttf`, `.otf`, `.woff`, and `.woff2` are supported
- Convert your font to a supported format if needed

### "No font files found in directory"
- Make sure font files are directly in the specified directory
- Check that files have a supported extension (.ttf, .otf, etc.)

### Fonts not appearing in output
- The font file may be corrupt or incompatible
- Try a different font or the default fonts
- Check console output for specific error messages

## Font Policy

When using custom fonts:
- Ensure you have the right to use the font for your intended purpose
- Respect font licenses and attribution requirements
- For commercial use, verify font licensing terms
- The generated posters include OpenStreetMap attribution by default

