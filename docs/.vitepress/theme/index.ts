// https://vitepress.dev/guide/custom-theme
import type { Theme } from 'vitepress'
import DefaultTheme from 'vitepress/theme'
import { onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vitepress'
import mediumZoom from 'medium-zoom'
import ImageGallery from './components/image-gallery.vue'
import './style.css'

export default {
  extends: DefaultTheme,
  setup() {
    const router = useRouter()
    let zoom: ReturnType<typeof mediumZoom> | null = null

    const setupMediumZoom = () => {
      nextTick(() => {
        if (zoom) {
          zoom.detach()
          zoom.close()
          zoom = null
        }
        setTimeout(() => {
          zoom = mediumZoom('.gallery-image', {
            background: 'transparent',
            margin: 24
          })
        }, 100)
      })
    }

    onMounted(() => {
      setupMediumZoom()
    })

    watch(
      () => router.route.path,
      () => {
        setupMediumZoom()
      }
    )
  },
  enhanceApp({ app, router, siteData }) {
    // Register global components
    app.component('ImageGallery', ImageGallery)
  }
} satisfies Theme
