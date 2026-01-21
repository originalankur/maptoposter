import { defineConfig } from 'vitepress'
import { galleryDataPlugin } from './plugins/gallery-data'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  vite: {
    plugins: [galleryDataPlugin()],
    ssr: {
      noExternal: ['medium-zoom']
    }
  },
  title: "City Map Poster Generator",
  description: "Generate beautiful, minimalist map posters for any city in the world",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Docs', link: '/installation' },
      { text: 'Gallery', link: '/gallery' }
    ],

    sidebar: [
      {
        text: 'Getting Started',
        items: [
          { text: 'Examples', link: '/examples' },
          { text: 'Installation', link: '/installation' },
          { text: 'Usage', link: '/usage' }
        ]
      },
      {
        text: 'Themes',
        items: [
          { text: 'Available Themes', link: '/themes' },
          { text: 'Custom Themes', link: '/custom-themes' }
        ]
      },
      {
        text: 'Reference',
        items: [
          { text: 'Output', link: '/output' },
          { text: 'Project Structure', link: '/project-structure' },
          { text: 'Hacker\'s Guide', link: '/hackers-guide' }
        ]
      },
      {
        text: 'Contributing',
        items: [
          { text: 'Contributing to Gallery', link: '/contributing-gallery' }
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/originalankur/maptoposter' }
    ]
  }
})
