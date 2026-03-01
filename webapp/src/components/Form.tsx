import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import CityAutocomplete from './CityAutocomplete'

interface FormProps {
  onGenerate: (data: any) => void
  loading: boolean
  error: string | null
  advancedOptions: boolean
  onToggleAdvanced: () => void
}

export default function Form({ onGenerate, loading, error, advancedOptions, onToggleAdvanced }: FormProps) {
  const { t } = useTranslation()
  const [formData, setFormData] = useState({
    city: '',
    country: '',
    distance: 18000,
    width: 12,
    height: 16,
    latitude: '',
    longitude: '',
    displayCity: '',
    displayCountry: '',
    fontFamily: ''
  })
  const [useAutocomplete, setUseAutocomplete] = useState(true)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validate city and country are selected
    if (!formData.city || !formData.country) {
      alert(t('form.selectCityAlert'))
      return
    }
    
    onGenerate({
      city: formData.city,
      country: formData.country,
      distance: parseInt(formData.distance.toString()),
      width: formData.width,
      height: formData.height,
      latitude: formData.latitude ? parseFloat(formData.latitude) : undefined,
      longitude: formData.longitude ? parseFloat(formData.longitude) : undefined,
      display_city: formData.displayCity || undefined,
      display_country: formData.displayCountry || undefined,
      font_family: formData.fontFamily || undefined
    })
  }

  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleCitySelect = (city: string, country: string, lat: string, lon: string) => {
    setFormData(prev => ({
      ...prev,
      city,
      country,
      latitude: lat,
      longitude: lon
    }))
  }

  return (
    <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 shadow-2xl border border-white/20">
      <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <span className="text-3xl">🗺️</span>
        {t('form.title')}
      </h2>

      <form onSubmit={handleSubmit} className="space-y-5">
        {useAutocomplete ? (
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium">
                {t('form.city')} {t('form.required')}
              </label>
              <button
                type="button"
                onClick={() => setUseAutocomplete(false)}
                className="text-xs text-purple-400 hover:text-purple-300"
              >
                Manual input
              </button>
            </div>
            <CityAutocomplete 
              onSelect={handleCitySelect}
              value={formData.city}
            />
            {formData.city && formData.country ? (
              <div className="mt-2 px-3 py-2 bg-green-500/20 border border-green-500/50 rounded-lg text-sm text-green-300">
                ✓ {t('form.citySelected')}: 📍 {formData.city}, {formData.country}
              </div>
            ) : (
              <div className="mt-2 px-3 py-2 bg-yellow-500/20 border border-yellow-500/50 rounded-lg text-sm text-yellow-300">
                ⚠️ {t('form.pleaseSelectCity')}
              </div>
            )}
          </div>
        ) : (
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium">
                {t('form.city')} & {t('form.country')} {t('form.required')}
              </label>
              <button
                type="button"
                onClick={() => setUseAutocomplete(true)}
                className="text-xs text-purple-400 hover:text-purple-300"
              >
                🔍 Use search
              </button>
            </div>
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <input
                  type="text"
                  value={formData.city}
                  onChange={(e) => handleChange('city', e.target.value)}
                  placeholder={t('form.cityPlaceholder')}
                  className="w-full px-4 py-3 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-white/50"
                  required
                />
              </div>
              <div>
                <input
                  type="text"
                  value={formData.country}
                  onChange={(e) => handleChange('country', e.target.value)}
                  placeholder={t('form.countryPlaceholder')}
                  className="w-full px-4 py-3 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-white/50"
                  required
                />
              </div>
            </div>
          </div>
        )}

        <div>
          <label className="block text-sm font-medium mb-2">
            {t('form.mapRadius')}: {formData.distance}m
          </label>
          <input
            type="range"
            min="4000"
            max="20000"
            step="1000"
            value={formData.distance}
            onChange={(e) => handleChange('distance', parseInt(e.target.value))}
            className="w-full h-2 bg-white/20 rounded-lg appearance-none cursor-pointer"
          />
          <div className="flex justify-between text-xs text-slate-400 mt-1">
            <span>{t('form.denseCenter')}</span>
            <span>{t('form.largeMetro')}</span>
          </div>
        </div>

        {advancedOptions && (
          <div className="space-y-4 p-4 bg-black/20 rounded-lg">
            <h3 className="font-medium text-sm text-slate-300">{t('form.advancedOptions')}</h3>
            
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm mb-2">{t('form.width')}:</label>
                <input
                  type="number"
                  min="3.6"
                  max="20"
                  step="0.1"
                  value={formData.width}
                  onChange={(e) => handleChange('width', parseFloat(e.target.value))}
                  className="w-full px-3 py-2 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
              <div>
                <label className="block text-sm mb-2">{t('form.height')}:</label>
                <input
                  type="number"
                  min="3.6"
                  max="20"
                  step="0.1"
                  value={formData.height}
                  onChange={(e) => handleChange('height', parseFloat(e.target.value))}
                  className="w-full px-3 py-2 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
            </div>

            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm mb-2">{t('form.latitude')}:</label>
                <input
                  type="number"
                  step="any"
                  value={formData.latitude}
                  onChange={(e) => handleChange('latitude', e.target.value)}
                  placeholder="e.g., 48.8566"
                  className="w-full px-3 py-2 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
              <div>
                <label className="block text-sm mb-2">{t('form.longitude')}:</label>
                <input
                  type="number"
                  step="any"
                  value={formData.longitude}
                  onChange={(e) => handleChange('longitude', e.target.value)}
                  placeholder="e.g., 2.3522"
                  className="w-full px-3 py-2 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
            </div>

            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm mb-2">{t('form.displayCity')}:</label>
                <input
                  type="text"
                  value={formData.displayCity}
                  onChange={(e) => handleChange('displayCity', e.target.value)}
                  placeholder="e.g., パリ"
                  className="w-full px-3 py-2 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
              <div>
                <label className="block text-sm mb-2">{t('form.displayCountry')}:</label>
                <input
                  type="text"
                  value={formData.displayCountry}
                  onChange={(e) => handleChange('displayCountry', e.target.value)}
                  placeholder="e.g., フランス"
                  className="w-full px-3 py-2 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm mb-2">{t('form.fontFamily')}:</label>
              <input
                type="text"
                value={formData.fontFamily}
                onChange={(e) => handleChange('fontFamily', e.target.value)}
                placeholder="e.g., Noto Sans JP"
                className="w-full px-3 py-2 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
          </div>
        )}

        <button
          type="button"
          onClick={onToggleAdvanced}
          className="text-sm text-purple-400 hover:text-purple-300 transition-colors"
        >
          {advancedOptions ? t('form.hideAdvanced') : t('form.showAdvanced')} ▾
        </button>

        {error && (
          <div className="p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-300 text-sm">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-4 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg font-bold text-lg transition-all duration-300 shadow-lg hover:shadow-xl"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              {t('form.generating')}
            </span>
          ) : (
            `${t('form.generate')} 🎨`
          )}
        </button>
      </form>
    </div>
  )
}