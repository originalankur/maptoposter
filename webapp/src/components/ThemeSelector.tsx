import { useTranslation } from 'react-i18next'

interface Theme {
  name: string
  description?: string
  preview_colors?: string[]
}

interface ThemeSelectorProps {
  themes: Theme[]
  selectedTheme: string
  onSelectTheme: (theme: string) => void
}

export default function ThemeSelector({ themes, selectedTheme, onSelectTheme }: ThemeSelectorProps) {
  const { t } = useTranslation()
  
  return (
    <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 shadow-2xl border border-white/20">
      <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
        <span className="text-3xl">🎨</span>
        {t('theme.title')}
      </h2>
      <p className="text-sm text-slate-400 mb-4">{t('theme.description')}</p>
      
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
        {themes.map((theme) => (
          <button
            key={theme.name}
            onClick={() => onSelectTheme(theme.name)}
            className={`p-3 rounded-xl border-2 transition-all duration-300 ${
              selectedTheme === theme.name
                ? 'border-purple-500 bg-purple-500/20 scale-105'
                : 'border-white/20 hover:border-purple-400 hover:scale-102'
            }`}
          >
            {theme.preview_colors && theme.preview_colors.length > 0 && (
              <div className="flex gap-1 mb-2">
                {theme.preview_colors.slice(0, 4).map((color, idx) => (
                  <div
                    key={idx}
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
            )}
            <div className="text-sm font-medium text-center">
              {theme.name.replace('_', ' ')}
            </div>
          </button>
        ))}
      </div>

      {themes.find(t => t.name === selectedTheme)?.description && (
        <div className="mt-4 p-3 bg-black/20 rounded-lg">
          <p className="text-sm text-slate-300">
            {themes.find(t => t.name === selectedTheme)?.description}
          </p>
        </div>
      )}
    </div>
  )
}