# Contributing to the Gallery

Thank you for your interest in contributing to the Map2Poster gallery! This guide will walk you through the process of adding your city poster to the gallery.

## Overview

The gallery is organized by continents in separate markdown files:
- `gallery-europe.md` - European cities
- `gallery-asia.md` - Asian cities
- `gallery-north-america.md` - North American cities
- `gallery-africa.md` - African cities
- `gallery-oceania.md` - Oceanian cities

## Step-by-Step Guide

### Prepare Your Image

You have two options for hosting your poster image:

#### Option 1: Copy to Public Directory

Copy your generated poster image to the `docs/public/` directory:

```bash
cp posters/city_theme_timestamp.png docs/public/
```

**Naming Convention:**
- Use lowercase with underscores: `city_theme_timestamp.png`
- Example: `tokyo_japanese_ink_20260118_142446.png`

#### Option 2: Use External CDN Link

You may specify an external CDN link pointing to an image. This is useful if:
- Your image is already hosted elsewhere
- You want to use a CDN for faster loading
- You prefer not to commit large image files to the repository

**Example CDN links:**
- GitHub raw: `https://raw.githubusercontent.com/username/repo/main/path/to/image.png`
- Imgur: `https://i.imgur.com/xxxxx.png`
- Cloudinary: `https://res.cloudinary.com/xxxxx/image/upload/xxxxx.png`
- Any other CDN or image hosting service

### Choose the Correct Gallery File

Edit the appropriate gallery file based on the continent:

- **Europe**: `docs/gallery-europe.md`
- **Asia**: `docs/gallery-asia.md`
- **North America**: `docs/gallery-north-america.md`
- **Africa**: `docs/gallery-africa.md`
- **Oceania**: `docs/gallery-oceania.md`

### Add Your Image Link

Add your image to the gallery file using the `<ImageGallery>` component.

## Image Link Format

### New Format (Recommended)

Use this format to include all metadata for the copy command feature:

```markdown
![City Name | Country Name | Author | distance | theme](link-to-image.ext)
```

**Examples:**

Local image:
```markdown
![Tokyo | Japan | Map2Poster | 15000 | japanese_ink](/tokyo_japanese_ink_20260118_142446.png)
```

External CDN link:
```markdown
![Tokyo | Japan | Map2Poster | 15000 | japanese_ink](https://raw.githubusercontent.com/username/repo/main/tokyo_japanese_ink.png)
```

**Format Breakdown:**
- `City Name` - The name of the city (required)
- `Country Name` - The name of the country (required)
- `Author` - Your name or "Map2Poster" (required)
- `distance` - The distance value in meters used (optional, but recommended)
- `theme` - The theme name used (optional, but recommended)

### Old Format (Backwards Compatible)

For simpler entries without metadata:

```markdown
![City Name | Author](/image_filename.png)
```

**Examples:**

Local image:
```markdown
![Tokyo | Map2Poster](/tokyo_japanese_ink_20260118_142446.png)
```

External CDN link:
```markdown
![Tokyo | Map2Poster](https://example.com/cdn/tokyo_japanese_ink.png)
```

> **Note:** While the old format works, the new format is recommended as it enables the copy command feature and displays all flag details in the gallery.

### Complete Example

Here's a complete example of adding an entry to `gallery-asia.md`:

```markdown
---
continent: asia
---

# Asia Gallery

<ImageGallery>

![Tokyo | Japan | Map2Poster | 15000 | japanese_ink](/tokyo_japanese_ink_20260118_142446.png)
![Mumbai | India | Map2Poster | 18000 | contrast_zones](/mumbai_contrast_zones_20260118_145843.png)
![Singapore | Singapore | Map2Poster | 12000 | neon_cyberpunk](/singapore_neon_cyberpunk_20260118_153328.png)
![Your City | Your Country | Your Name | 10000 | your_theme](/your_city_your_theme_timestamp.png)

</ImageGallery>
```

## Frontmatter

Each gallery file must include frontmatter with the continent:

```markdown
---
continent: asia
---
```

Available continent values:
- `europe`
- `asia`
- `north-america`
- `africa`
- `oceania`

## Creating a Pull Request

1. **Fork the repository** (if you haven't already)
   
   Visit [https://github.com/originalankur/maptoposter](https://github.com/originalankur/maptoposter) and click the "Fork" button.

2. **Create a new branch:**
   ```bash
   git checkout -b add-gallery-entry-city-name
   ```

3. **Add your changes:**
   - Either copy your poster image to `docs/public/` OR use an external CDN link
   - Edit the appropriate gallery markdown file
   - Add your image link in the correct format (local path or CDN URL)

4. **Commit your changes:**
   ```bash
   # If using local image:
   git add docs/public/your_image.png
   git add docs/gallery-*.md
   git commit -m "Add [City Name] to gallery"
   
   # If using CDN link, only commit the markdown file:
   git add docs/gallery-*.md
   git commit -m "Add [City Name] to gallery"
   ```

5. **Push to your fork:**
   ```bash
   git push origin add-gallery-entry-city-name
   ```

6. **Create a Pull Request** on GitHub with:
   - A clear title: "Add [City Name] to [Continent] gallery"
   - Description of the city and theme used
   - Screenshot of the poster (optional but helpful)

## Tips

- **Image Quality**: Use high-quality PNG images (the tool generates 300 DPI by default)
- **Theme Selection**: Choose a theme that complements the city's character
- **Distance**: Adjust the distance parameter to capture the best view of the city
- **Consistency**: Follow the existing naming conventions and format
- **Testing**: Make sure your image displays correctly by running the VitePress dev server locally

## What Gets Displayed

When you use the new format, the gallery will automatically display:
- **City name** in the info bar
- **Country name** in the info bar
- **Distance** value in the info bar
- **Theme** name in the info bar
- **Copy button** that generates the exact command to reproduce the poster

This makes it easy for users to see how each poster was created and reproduce it themselves!

