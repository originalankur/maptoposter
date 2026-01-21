<template>
  <div class="image-gallery" ref="galleryRef">
    <!-- Hidden slot for parsing markdown images -->
    <div style="display: none; visibility: hidden; position: absolute;">
      <slot />
    </div>

    <!-- Continent Selector -->
    <div class="continent-selector">
      <button
        v-for="continent in allContinents"
        :key="continent"
        :class="['continent-btn', { active: selectedContinent === continent }]"
        @click="selectedContinent = continent"
      >
        {{ formatContinentName(continent) }}
      </button>
    </div>

    <!-- Masonry Grid -->
    <div v-if="filteredImages.length > 0" class="masonry-container">
      <div
        v-for="(image, index) in filteredImages"
        :key="`${image.src}-${index}`"
        class="masonry-item"
      >
        <div class="image-wrapper">
          <div v-show="!imageLoaded[index]" class="skeleton-loader"></div>
          <img
            :src="image.src"
            :alt="`${image.title} by ${image.author}`"
            class="gallery-image"
            :class="{ 'image-loaded': imageLoaded[index] }"
            :data-city="image.title"
            :data-country="image.country || ''"
            :data-author="image.author"
            @load="imageLoaded[index] = true"
            @error="imageLoaded[index] = true"
          />
          <div class="image-overlay">
            <div class="overlay-content">
              <span class="image-title">{{ image.title }}</span>
              <span v-if="image.country" class="image-country">{{ image.country }}</span>
              <span class="image-author">by {{ image.author }}</span>
            </div>
          </div>
        </div>
        <div class="image-info-bar">
          <div class="info-items">
            <div v-if="image.title" class="info-item">
              <span class="info-label">city:</span>
              <span class="info-value">{{ image.title }}</span>
            </div>
            <div v-if="image.country" class="info-item">
              <span class="info-label">country:</span>
              <span class="info-value">{{ image.country }}</span>
            </div>
            <div v-if="image.distance" class="info-item">
              <span class="info-label">distance:</span>
              <span class="info-value">{{ image.distance }}</span>
            </div>
            <div v-if="image.theme" class="info-item">
              <span class="info-label">theme:</span>
              <span class="info-value">{{ image.theme }}</span>
            </div>
          </div>
          <button 
            class="copy-button" 
            @click="(e) => copyCommand(image, e, index)"
            :title="'Copy command to generate this image'"
          >
            <svg v-if="copiedIndex !== index" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="copy-icon">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="check-icon">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <p>No images found for the selected continent.</p>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useGalleryData, type GalleryImage } from '../composables/use-gallery-data'
import { useData } from 'vitepress'

const props = defineProps<{
  images?: GalleryImage[]
  continents?: string[]
}>()

const { frontmatter } = useData()
const galleryRef = ref<HTMLElement | null>(null)
const copiedIndex = ref<number | null>(null)
const imageLoaded = ref<Record<number, boolean>>({})

const {
  images: galleryImages,
  continents: galleryContinents,
  selectedContinent,
  filteredImages: galleryFilteredImages,
  loadGalleryData,
  parseImagesFromDOM
} = useGalleryData()

// Try to parse images from slot content if available
const parseSlotImages = async () => {
  await nextTick()
  await new Promise(resolve => setTimeout(resolve, 200))
  
  if (galleryRef.value) {
    const continent = (frontmatter.value.continent as string | undefined) || 'unknown'
    const parsed = parseImagesFromDOM(galleryRef.value, continent)
    if (parsed.length > 0) {
      // Merge with existing images, avoiding duplicates
      const existing = galleryImages.value
      const newImages = parsed.filter(p => !existing.some(e => e.src === p.src))
      galleryImages.value = [...existing, ...newImages]
      console.log(`[Gallery] Parsed ${parsed.length} images from slot (continent: ${continent})`)
    }
  }
}

// Use props if provided, otherwise use composable data
const images = computed(() => props.images || galleryImages.value)
const allContinents = computed(() => {
  if (props.continents) {
    return ['all', ...props.continents]
  }
  return ['all', ...galleryContinents.value]
})

const filteredImages = computed(() => {
  if (props.images) {
    // If images are provided via props, filter them
    if (selectedContinent.value === 'all') {
      return props.images
    }
    return props.images.filter(img => img.continent === selectedContinent.value)
  }
  return galleryFilteredImages.value
})

const formatContinentName = (continent: string): string => {
  if (continent === 'all') return 'All'
  return continent
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

const copyCommand = async (image: GalleryImage, event: Event, index: number) => {
  // Generate command: python create_map_poster.py -c "City" -C "Country" -t theme -d distance
  const city = image.title
  const country = image.country || 'Unknown'
  const theme = image.theme || 'feature_based'
  const distance = image.distance || '29000'
  
  const command = `python create_map_poster.py -c "${city}" -C "${country}" -t ${theme} -d ${distance}`
  
  try {
    await navigator.clipboard.writeText(command)
    // Show checkmark
    copiedIndex.value = index
    setTimeout(() => {
      copiedIndex.value = null
    }, 2000)
  } catch (err) {
    console.error('Failed to copy command:', err)
    // Fallback: show command in alert
    alert(`Command:\n${command}\n\n(Manually copy this command)`)
  }
}
onMounted(async () => {
  // Load gallery data (will try JSON first, then runtime parsing)
  if (!props.images) {
    // First try to load from all sources
    await loadGalleryData()
    
    // Also try parsing from slot (for individual gallery pages or main gallery)
    await parseSlotImages()
    
    // If still no images, wait a bit more and try again (for slow loading)
    if (galleryImages.value.length === 0) {
      await new Promise(resolve => setTimeout(resolve, 500))
      await parseSlotImages()
      if (galleryImages.value.length === 0) {
        await loadGalleryData()
      }
    }
    
    console.log(`[Gallery] Total images loaded: ${galleryImages.value.length}`)
    console.log(`[Gallery] Continents:`, galleryContinents.value)
  }
})

</script>

<style scoped>
.image-gallery {
  width: 100%;
}

.continent-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--vp-c-divider);
}

.continent-btn {
  padding: 8px 16px;
  border: 1px solid var(--vp-c-divider);
  background: var(--vp-c-bg);
  color: var(--vp-c-text-1);
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
  font-weight: 500;
}

.continent-btn:hover {
  background: var(--vp-c-bg-soft);
  border-color: var(--vp-c-brand);
}

.continent-btn.active {
  background: var(--vp-c-brand);
  color: var(--vp-c-brand-text);
  border-color: var(--vp-c-brand);
}

.masonry-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 16px;
  grid-auto-rows: auto;
  align-items: start;
}

.masonry-item {
  position: relative;
  border-radius: 8px;
  overflow: visible;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  display: flex;
  flex-direction: column;
}

.image-wrapper {
  position: relative;
  width: 100%;
  overflow: hidden;
  border-radius: 8px 8px 0 0;
  background: var(--vp-c-bg);
  min-height: 200px;
  pointer-events: auto;
}

.skeleton-loader {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  min-height: 200px;
  background: linear-gradient(
    90deg,
    var(--vp-c-bg-soft) 0%,
    var(--vp-c-bg) 50%,
    var(--vp-c-bg-soft) 100%
  );
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s ease-in-out infinite;
  border-radius: 8px 8px 0 0;
  z-index: 1;
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.gallery-image {
  width: 100%;
  height: auto;
  display: block;
  object-fit: cover;
  transition: opacity 0.3s ease, transform 0.3s ease;
  cursor: zoom-in;
  opacity: 0;
  position: relative;
  z-index: 2;
  pointer-events: auto;
}

.gallery-image.image-loaded {
  opacity: 1;
}

.image-wrapper:hover .gallery-image {
  transform: scale(1.05);
}

.image-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.8), transparent);
  color: white;
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
  z-index: 3;
}

.image-wrapper:hover .image-overlay {
  opacity: 1;
}

.overlay-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.image-title {
  font-weight: 600;
  font-size: 16px;
  line-height: 1.4;
}

.image-country {
  font-size: 14px;
  opacity: 0.95;
  line-height: 1.4;
}

.image-author {
  font-size: 13px;
  opacity: 0.9;
  line-height: 1.4;
}


.image-info-bar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 12px 16px;
  background: var(--vp-c-bg-soft);
  border-top: 1px solid var(--vp-c-divider);
  gap: 12px;
  border-radius: 0 0 8px 8px;
  min-height: fit-content;
  width: 100%;
  box-sizing: border-box;
}

.info-items {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  flex: 1;
  min-width: 0;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  white-space: nowrap;
  flex-shrink: 0;
}

.info-label {
  color: var(--vp-c-text-2);
  font-weight: 500;
  text-transform: lowercase;
}

.info-value {
  color: var(--vp-c-text-1);
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  word-break: break-word;
}

.copy-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  background: var(--vp-c-bg);
  border: 1px solid var(--vp-c-divider);
  border-radius: 6px;
  color: var(--vp-c-text-1);
  cursor: pointer;
  transition: all 0.2s ease;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  align-self: flex-start;
}

.copy-button:hover {
  background: var(--vp-c-bg-soft);
  border-color: var(--vp-c-brand);
  color: var(--vp-c-brand);
}

.copy-button:active {
  transform: scale(0.98);
}

.copy-button svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.copy-button .check-icon {
  color: #10b981;
  stroke: #10b981;
}

.empty-state {
  text-align: center;
  padding: 48px 24px;
  color: var(--vp-c-text-2);
}

.empty-state p {
  margin: 0;
  font-size: 16px;
}


/* Responsive adjustments */
@media (max-width: 768px) {
  .masonry-container {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 12px;
  }

  .continent-selector {
    gap: 6px;
  }

  .continent-btn {
    padding: 6px 12px;
    font-size: 13px;
  }

  .image-info-bar {
    padding: 10px 12px;
    flex-direction: column;
    align-items: stretch;
  }

  .info-items {
    gap: 12px;
    width: 100%;
  }

  .copy-button {
    width: 32px;
    height: 32px;
    justify-content: center;
    margin-top: 8px;
    align-self: flex-end;
  }
}

</style>
