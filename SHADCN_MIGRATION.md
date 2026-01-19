# Shadcn UI Migration Guide

## What's Been Set Up

1. **Tailwind Configuration** - `tailwind.config.js` with dark theme support
2. **PostCSS Configuration** - `postcss.config.js` for Tailwind processing
3. **Dependencies** - Updated `package.json` with all shadcn/ui dependencies
4. **Utils** - Created `src/lib/utils.js` with cn() helper

## Next Steps to Complete Migration

### 1. Update index.css with Dark Theme Variables

Replace `frontend/src/index.css` with:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 221.2 83.2% 53.3%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 217.2 91.2% 59.8%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 224.3 76.3% 48%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

### 2. Install Dependencies

```bash
cd frontend
npm install
```

### 3. Create Shadcn Components

Run these commands to add shadcn components:
```bash
npx shadcn-ui@latest init
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add input
npx shadcn-ui@latest add label
npx shadcn-ui@latest add slider
npx shadcn-ui@latest add checkbox
npx shadcn-ui@latest add radio-group
npx shadcn-ui@latest add separator
npx shadcn-ui@latest add tabs
npx shadcn-ui@latest add accordion
npx shadcn-ui@latest add select
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add progress
```

### 4. Key Features to Implement

**Enhanced Backend Progress Updates:**
- Add granular progress tracking for each step
- Return detailed status messages
- Track: Queued → Geocoding → Street Network → Water → Parks → Buildings → Railways → Rendering → Saving → Complete

**Dark Theme UI:**
- Use dark background colors
- Add theme cards with color palettes
- Implement responsive grid layout

**Detailed Progress Panel:**
- Show step-by-step progress
- Add check marks for completed steps
- Show current step with loading indicator
- Display estimated time remaining

**Modern Form Controls:**
- Use shadcn Button, Input, Label
- Implement Slider for distance
- Use Select for themes
- Add Accordion for advanced options

## Architecture

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # Shadcn components
│   │   ├── ThemeCard.jsx    # Custom theme card
│   │   └── ProgressTracker.jsx # Detailed progress
│   ├── lib/
│   │   └── utils.js         # cn() utility
│   ├── App.jsx              # Main app with new UI
│   └── index.css            # Dark theme variables
├── tailwind.config.js
├── postcss.config.js
└── package.json
```

## Benefits

- Modern, professional UI
- Consistent component library
- Dark theme by default
- Accessible components
- Better UX with detailed progress
- Easier to maintain and extend
