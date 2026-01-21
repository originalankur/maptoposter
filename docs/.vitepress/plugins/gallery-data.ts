import type { Plugin } from 'vite'
import { readFileSync, readdirSync, existsSync, mkdirSync, writeFileSync } from 'fs'
import { join, resolve } from 'path'

interface GalleryImage {
  src: string
  title: string
  author: string
  continent: string
  country?: string
  distance?: string
  theme?: string
}

function generateGalleryData() {
  // This runs at build time and dev server start
  // When running from docs/, process.cwd() is already the docs directory
  // When running from root, we need to resolve to docs/
  let docsDir = process.cwd()
  
  // Check if we're in the docs directory or root directory
  // The config file is in .vitepress/, so we need to go up one level to get to docs/
  try {
    // Check if gallery files exist in current directory
    if (!existsSync(join(docsDir, 'gallery-north-america.md'))) {
      // If not found, try parent directory (if running from project root)
      const parentDir = resolve(docsDir, '..')
      if (existsSync(join(parentDir, 'gallery-north-america.md'))) {
        docsDir = parentDir
      } else {
        // Try docs subdirectory (if running from project root)
        const docsSubDir = join(docsDir, 'docs')
        if (existsSync(join(docsSubDir, 'gallery-north-america.md'))) {
          docsDir = docsSubDir
        }
      }
    }
  } catch (e) {
    // Fallback: assume we're in docs directory
    console.warn('[gallery-data-plugin] Could not determine docs directory, using cwd:', e)
  }
  
  const galleryFiles: GalleryImage[] = []

  try {
    // Find all gallery-*.md files
    const files = readdirSync(docsDir).filter(f => 
      f.startsWith('gallery-') && f.endsWith('.md')
    )

    for (const file of files) {
      const filePath = join(docsDir, file)
      const content = readFileSync(filePath, 'utf-8')
      
      // Extract frontmatter
      const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/)
      const frontmatter = frontmatterMatch ? frontmatterMatch[1] : ''
      const continent = frontmatter.match(/continent:\s*(.+)/)?.[1]?.trim() || 'unknown'
      
      // Extract images: ![title|author](url)
      const imageRegex = /!\[([^\]]+)\]\(([^)]+)\)/g
      let match
      
      while ((match = imageRegex.exec(content)) !== null) {
        const altText = match[1]
        const imageSrc = match[2]
        
        // Parse format: 
        // New: title|country|author|distance|theme
        // Old: title|author (backwards compatibility)
        const parts = altText.split('|').map(s => s.trim())
        let title, country, author, distance, theme
        
        if (parts.length >= 5) {
          // New format: title|country|author|distance|theme
          title = parts[0] || 'Untitled'
          country = parts[1] || undefined
          author = parts[2] || 'Unknown'
          distance = parts[3] || undefined
          theme = parts[4] || undefined
        } else if (parts.length === 2) {
          // Old format: title|author
          title = parts[0] || 'Untitled'
          country = undefined
          author = parts[1] || 'Unknown'
          distance = undefined
          theme = undefined
        } else {
          // Fallback: just title
          title = parts[0] || 'Untitled'
          country = parts[1] || undefined
          author = parts[2] || 'Unknown'
          distance = parts[3] || undefined
          theme = parts[4] || undefined
        }
        
        // Normalize image path
        const normalizedSrc = imageSrc.startsWith('http') 
          ? imageSrc 
          : (imageSrc.startsWith('/') ? imageSrc : '/' + imageSrc)
        
        galleryFiles.push({
          src: normalizedSrc,
          title: title,
          author: author,
          continent: continent,
          country: country,
          distance: distance,
          theme: theme
        })
      }
    }

    // Write the data to a JSON file in public directory
    const publicDir = join(docsDir, 'public')
    if (!existsSync(publicDir)) {
      mkdirSync(publicDir, { recursive: true })
    }
    
    const outputPath = join(publicDir, 'gallery-data.json')
    writeFileSync(outputPath, JSON.stringify(galleryFiles, null, 2), 'utf-8')
    
    console.log(`[gallery-data-plugin] Generated gallery data with ${galleryFiles.length} images`)
  } catch (error) {
    console.warn('[gallery-data-plugin] Failed to generate gallery data:', error)
  }
}

export function galleryDataPlugin(): Plugin {
  return {
    name: 'gallery-data-plugin',
    buildStart() {
      generateGalleryData()
    },
    configureServer() {
      // Also generate in dev mode
      generateGalleryData()
    },
    handleHotUpdate({ file }) {
      if (file.includes('gallery-') && file.endsWith('.md')) {
        generateGalleryData()
      }
    }
  }
}
