import { computed, ref } from 'vue'
import { useData } from 'vitepress'

export interface GalleryImage {
  src: string
  title: string
  author: string
  continent: string
  country?: string
  distance?: string
  theme?: string
}

/**
 * Gallery Data Composable
 * 
 * Architecture:
 * 1. Primary: Loads from gallery-data.json (generated at build-time by gallery-data plugin)
 *    - Fast, reliable, works in production
 *    - Automatically regenerated when gallery-*.md files change
 * 
 * 2. Fallback: DOM parsing (development mode only)
 *    - Used when JSON file doesn't exist yet
 *    - Parses images from rendered HTML
 *    - Less reliable but works without build step
 * 
 * The build-time plugin (gallery-data.ts) scans all gallery-*.md files,
 * extracts images and frontmatter, and generates gallery-data.json.
 * This approach is more maintainable than runtime parsing because:
 * - Single source of truth (markdown files)
 * - No hardcoded file lists
 * - Automatic discovery of new gallery files
 * - Type-safe data structure
 */
export function useGalleryData() {
  const { site } = useData()
  const images = ref<GalleryImage[]>([])
  const selectedContinent = ref<string>('all')

  // Parse images from DOM (when component is used with markdown images in slot)
  const parseImagesFromDOM = (container: HTMLElement | null, continent?: string) => {
    if (!container) return []

    const imgElements = container.querySelectorAll('img')
    const parsedImages: GalleryImage[] = []

    imgElements.forEach((img) => {
      const altText = img.getAttribute('alt') || ''
      const src = img.getAttribute('src') || img.src
      
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
      
      parsedImages.push({
        src: src,
        title: title,
        author: author,
        continent: continent || 'unknown',
        country: country,
        distance: distance,
        theme: theme
      })
    })

    return parsedImages
  }

  /**
   * Load gallery data from the generated JSON file (primary method).
   * The JSON is generated at build-time by the gallery-data plugin.
   * Falls back to fetching markdown files directly if JSON is unavailable.
   */
  const loadGalleryData = async () => {
    try {
      // Primary: Load from build-time generated JSON file
      const response = await fetch('/gallery-data.json')
      if (response.ok) {
        const data = await response.json()
        if (Array.isArray(data) && data.length > 0) {
          images.value = data
          console.log(`[Gallery] Loaded ${data.length} images from gallery-data.json`)
          return
        }
      }
    } catch (error) {
      // JSON file doesn't exist - will try fallback
      console.debug('[Gallery] gallery-data.json not found, trying fallback methods')
    }

    // Fallback: Try to fetch and parse markdown files directly
    await parseFromMarkdownFiles()
  }

  /**
   * Parse images by fetching gallery-*.md files directly.
   * This is a fallback when gallery-data.json isn't available.
   */
  const parseFromMarkdownFiles = async () => {
    const allImages: GalleryImage[] = []
    const galleryFileNames = [
      'gallery-north-america',
      'gallery-europe', 
      'gallery-asia',
      'gallery-africa',
      'gallery-oceania'
    ]
    
    for (const fileName of galleryFileNames) {
      try {
        // Try different possible paths
        const possiblePaths = [
          `/${fileName}.md`,
          `/docs/${fileName}.md`,
          fileName + '.md'
        ]
        
        let content = ''
        for (const path of possiblePaths) {
          try {
            const response = await fetch(path)
            if (response.ok) {
              content = await response.text()
              break
            }
          } catch (e) {
            // Try next path
          }
        }
        
        if (!content) {
          console.debug(`[Gallery] Could not fetch ${fileName}.md`)
          continue
        }
        
        // Extract frontmatter
        const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/)
        const frontmatter = frontmatterMatch ? frontmatterMatch[1] : ''
        const continentMatch = frontmatter.match(/continent:\s*(.+)/)
        const continent = continentMatch ? continentMatch[1].trim() : 'unknown'
        
        // Parse images: ![title|author](url)
        const imageRegex = /!\[([^\]]+)\]\(([^)]+)\)/g
        let match
        
        while ((match = imageRegex.exec(content)) !== null) {
          const altText = match[1]
          const imageSrc = match[2]
          
          // Parse format: title|country|author|distance|theme
          const parts = altText.split('|').map(s => s.trim())
          const title = parts[0] || 'Untitled'
          const country = parts[1] || undefined
          const author = parts[2] || 'Unknown'
          const distance = parts[3] || undefined
          const theme = parts[4] || undefined
          
          const normalizedSrc = imageSrc.startsWith('http') 
            ? imageSrc 
            : (imageSrc.startsWith('/') ? imageSrc : '/' + imageSrc)
          
          if (!allImages.some(i => i.src === normalizedSrc)) {
            allImages.push({
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
      } catch (error) {
        console.debug(`[Gallery] Error parsing ${fileName}:`, error)
      }
    }
    
    if (allImages.length > 0) {
      images.value = allImages
      console.log(`[Gallery] Loaded ${allImages.length} images from markdown files`)
    } else {
      // Final fallback: try DOM parsing
      console.debug('[Gallery] No images from markdown files, trying DOM parsing')
      await parseFromCurrentPage()
    }
  }

  /**
   * Parse images from the current page's DOM.
   * This is a fallback method used in development mode when gallery-data.json
   * hasn't been generated yet. It extracts images from the rendered HTML.
   */
  const parseFromCurrentPage = async () => {
    // Wait for DOM to be ready
    await new Promise(resolve => setTimeout(resolve, 800))
    
    const allImages: GalleryImage[] = []
    
    // Strategy 1: Try to find images in hidden slot (from ImageGallery component)
    const hiddenSlot = document.querySelector('.image-gallery [style*="display: none"], .image-gallery [style*="visibility: hidden"]')
    if (hiddenSlot) {
      const slotImages = hiddenSlot.querySelectorAll('img')
      slotImages.forEach((img) => {
        const altText = (img as HTMLImageElement).getAttribute('alt') || ''
        const src = (img as HTMLImageElement).getAttribute('src') || (img as HTMLImageElement).src
        
        if (!altText.includes('|')) return
        
        // Get continent from frontmatter if available, or infer from URL
        const pagePath = window.location.pathname
        let continent = 'unknown'
        if (pagePath.includes('gallery-')) {
          const match = pagePath.match(/gallery-([^/]+)/)
          if (match) {
            continent = match[1].replace(/-/g, ' ')
          }
        }
        
        // Parse format: title|country|author|distance|theme
        const parts = altText.split('|').map(s => s.trim())
        const title = parts[0] || 'Untitled'
        const country = parts[1] || undefined
        const author = parts[2] || 'Unknown'
        const distance = parts[3] || undefined
        const theme = parts[4] || undefined
        
        const normalizedSrc = src.startsWith('http') ? src : (src.startsWith('/') ? src : '/' + src)
        
        if (!allImages.some(i => i.src === normalizedSrc)) {
          allImages.push({
            src: normalizedSrc,
            title: title,
            author: author,
            continent: continent,
            country: country,
            distance: distance,
            theme: theme
          })
        }
      })
    }
    
    // Strategy 2: Last resort - look for any images in the main content
    if (allImages.length === 0) {
      const mainImages = document.querySelectorAll('main img')
      mainImages.forEach((img) => {
        const altText = (img as HTMLImageElement).getAttribute('alt') || ''
        const src = (img as HTMLImageElement).getAttribute('src') || (img as HTMLImageElement).src
        
        if (!altText.includes('|')) return
        
        const pagePath = window.location.pathname
        let continent = 'unknown'
        if (pagePath.includes('gallery-')) {
          const match = pagePath.match(/gallery-([^/]+)/)
          if (match) {
            continent = match[1].replace(/-/g, ' ')
          }
        }
        
        // Parse format: title|country|author|distance|theme
        const parts = altText.split('|').map(s => s.trim())
        const title = parts[0] || 'Untitled'
        const country = parts[1] || undefined
        const author = parts[2] || 'Unknown'
        const distance = parts[3] || undefined
        const theme = parts[4] || undefined
        
        const normalizedSrc = src.startsWith('http') ? src : (src.startsWith('/') ? src : '/' + src)
        
        if (!allImages.some(i => i.src === normalizedSrc)) {
          allImages.push({
            src: normalizedSrc,
            title: title,
            author: author,
            continent: continent,
            country: country,
            distance: distance,
            theme: theme
          })
        }
      })
    }
    
    if (allImages.length > 0) {
      images.value = allImages
      console.log(`[Gallery] Parsed ${allImages.length} images from DOM (fallback mode)`)
    } else {
      console.warn('[Gallery] No images found. Make sure gallery-data.json is generated or restart the dev server.')
    }
  }

  // Get unique continents
  const continents = computed(() => {
    const unique = new Set(images.value.map(img => img.continent))
    return Array.from(unique).sort()
  })

  // Filter images by selected continent
  const filteredImages = computed(() => {
    if (selectedContinent.value === 'all') {
      return images.value
    }
    return images.value.filter(img => img.continent === selectedContinent.value)
  })


  return {
    images,
    continents,
    selectedContinent,
    filteredImages,
    loadGalleryData,
    parseImagesFromDOM
  }
}
