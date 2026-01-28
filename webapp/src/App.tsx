import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import axios from 'axios'
import ThemeSelector from './components/ThemeSelector'
import PosterPreview from './components/PosterPreview'
import Form from './components/Form'
import LanguageSwitcher from './components/LanguageSwitcher'
import ProgressBar from './components/ProgressBar'

interface Theme {
  name: string
  description?: string
  preview_colors?: string[]
}

interface Poster {
  filename: string
  url: string
  created: string
  size_bytes: number
}

export default function App() {
  const { t } = useTranslation()
  const [themes, setThemes] = useState<Theme[]>([])
  const [selectedTheme, setSelectedTheme] = useState('terracotta')
  const [posters, setPosters] = useState<Poster[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentPoster, setCurrentPoster] = useState<string | null>(null)
  const [advancedOptions, setAdvancedOptions] = useState(false)

  useEffect(() => {
    fetchThemes()
    fetchPosters()
  }, [])

  const fetchThemes = async () => {
    try {
      const response = await axios.get('/api/themes')
      setThemes(response.data)
    } catch (err) {
      console.error('Failed to fetch themes:', err)
    }
  }

  const fetchPosters = async () => {
    try {
      const response = await axios.get('/api/posters')
      setPosters(response.data)
    } catch (err) {
      console.error('Failed to fetch posters:', err)
    }
  }

  const handleGenerate = async (formData: any) => {
    setLoading(true)
    setError(null)
    setCurrentPoster(null)

    try {
      const response = await axios.post('/api/generate', {
        ...formData,
        theme: selectedTheme
      })

      if (response.data.success) {
        setCurrentPoster(response.data.url)
        await fetchPosters()
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate poster')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (filename: string) => {
    try {
      await axios.delete(`/api/posters/${filename}`)
      if (currentPoster?.includes(filename)) {
        setCurrentPoster(null)
      }
      await fetchPosters()
    } catch (err) {
      console.error('Failed to delete poster:', err)
    }
  }

  return (
    <>
      <ProgressBar isGenerating={loading} />
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
        <div className="container mx-auto px-4 py-8 max-w-7xl">
        <header className="text-center mb-8">
          <div className="flex justify-end mb-4">
            <LanguageSwitcher />
          </div>
          <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 bg-clip-text text-transparent">
            {t('app.title')}
          </h1>
          <p className="text-slate-300 text-lg">
            {t('app.subtitle')}
          </p>
        </header>

        <div className="grid lg:grid-cols-2 gap-8">
          <div className="space-y-6">
            <Form
              onGenerate={handleGenerate}
              loading={loading}
              error={error}
              advancedOptions={advancedOptions}
              onToggleAdvanced={() => setAdvancedOptions(!advancedOptions)}
            />

            <ThemeSelector
              themes={themes}
              selectedTheme={selectedTheme}
              onSelectTheme={setSelectedTheme}
            />
          </div>

          <div className="space-y-6">
            <PosterPreview
              currentPoster={currentPoster}
              posters={posters}
              loading={loading}
              onDelete={handleDelete}
            />
          </div>
        </div>

        <footer className="text-center mt-16 text-slate-400">
          <p>{t('app.footer')}</p>
        </footer>
        </div>
      </div>
    </>
  )
}