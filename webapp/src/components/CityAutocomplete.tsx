import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import axios from 'axios'

interface City {
  display_name: string
  name: string
  country: string
  lat: string
  lon: string
  address: {
    city?: string
    town?: string
    village?: string
    municipality?: string
    country?: string
    state?: string
  }
}

interface CityAutocompleteProps {
  onSelect: (city: string, country: string, lat: string, lon: string) => void
  value: string
}

export default function CityAutocomplete({ onSelect, value }: CityAutocompleteProps) {
  const { t, i18n } = useTranslation()
  const [query, setQuery] = useState(value)
  const [results, setResults] = useState<City[]>([])
  const [showResults, setShowResults] = useState(false)
  const [loading, setLoading] = useState(false)
  const [hasSelected, setHasSelected] = useState(false)
  const wrapperRef = useRef<HTMLDivElement>(null)
  const debounceTimer = useRef<number>()

  useEffect(() => {
    setQuery(value)
    // If value changes externally and is empty, reset selection state
    if (!value) {
      setHasSelected(false)
    }
  }, [value])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setShowResults(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const searchCities = async (searchQuery: string) => {
    if (searchQuery.length < 2) {
      setResults([])
      return
    }

    setLoading(true)
    try {
      // Use our backend proxy to avoid CORS and User-Agent issues
      // Pass current language for better search results
      const response = await axios.get('/api/search/cities', {
        params: {
          q: searchQuery,
          lang: i18n.language // zh, en, ja, etc.
        }
      })

      setResults(response.data)
      setShowResults(true)
    } catch (error) {
      console.error('Failed to search cities:', error)
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setQuery(value)
    setHasSelected(false) // Reset selection state when user types
    
    // Clear city data if user modifies the input
    if (hasSelected) {
      onSelect('', '', '', '')
    }

    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current)
    }

    debounceTimer.current = setTimeout(() => {
      searchCities(value)
    }, 300)
  }

  const handleSelect = (city: City) => {
    const cityName = city.address.city || 
                     city.address.town || 
                     city.address.village || 
                     city.address.municipality ||
                     city.name
    const country = city.address.country || ''
    
    setQuery(cityName)
    setShowResults(false)
    setHasSelected(true)
    onSelect(cityName, country, city.lat, city.lon)
  }

  return (
    <div ref={wrapperRef} className="relative">
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={handleInputChange}
          onFocus={() => results.length > 0 && setShowResults(true)}
          placeholder={t('form.searchCity')}
          className="w-full px-4 py-3 pr-10 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-white/50"
        />
        {loading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          </div>
        )}
        {!loading && query && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 text-white/50">
            🔍
          </div>
        )}
      </div>

      {showResults && results.length > 0 && (
        <div className="absolute z-50 w-full mt-2 bg-slate-800 border border-white/20 rounded-lg shadow-2xl max-h-80 overflow-y-auto">
          {results.map((city, index) => {
            const cityName = city.address.city || 
                           city.address.town || 
                           city.address.village || 
                           city.address.municipality ||
                           city.name
            const country = city.address.country || ''
            const state = city.address.state

            return (
              <button
                key={index}
                onClick={() => handleSelect(city)}
                className="w-full px-4 py-3 text-left hover:bg-white/10 transition-colors border-b border-white/10 last:border-b-0"
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">📍</span>
                  <div className="flex-1">
                    <div className="font-medium text-white">{cityName}</div>
                    <div className="text-sm text-slate-400">
                      {state && `${state}, `}{country}
                    </div>
                  </div>
                </div>
              </button>
            )
          })}
        </div>
      )}

      {showResults && results.length === 0 && query.length >= 2 && !loading && (
        <div className="absolute z-50 w-full mt-2 bg-slate-800 border border-white/20 rounded-lg shadow-2xl p-4 text-center text-slate-400">
          {t('form.noResults')}
        </div>
      )}
    </div>
  )
}
