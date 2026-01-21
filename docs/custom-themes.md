# Adding Custom Themes

Create a JSON file in `themes/` directory:

```json
{
  "name": "My Theme",
  "description": "Description of the theme",
  "bg": "#FFFFFF",
  "text": "#000000",
  "gradient_color": "#FFFFFF",
  "water": "#C0C0C0",
  "parks": "#F0F0F0",
  "road_motorway": "#0A0A0A",
  "road_primary": "#1A1A1A",
  "road_secondary": "#2A2A2A",
  "road_tertiary": "#3A3A3A",
  "road_residential": "#4A4A4A",
  "road_default": "#3A3A3A"
}
```

## Theme Properties

- `name`: Display name of the theme
- `description`: Description of the theme style
- `bg`: Background color (hex format)
- `text`: Text color for labels
- `gradient_color`: Color used for top/bottom gradient fades
- `water`: Color for water bodies
- `parks`: Color for parks and green spaces
- `road_motorway`: Color for motorways (thickest roads)
- `road_primary`: Color for primary roads
- `road_secondary`: Color for secondary roads
- `road_tertiary`: Color for tertiary roads
- `road_residential`: Color for residential streets
- `road_default`: Default color for unclassified roads
