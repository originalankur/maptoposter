import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'

interface Poster {
  filename: string
  url: string
  created: string
  size_bytes: number
}

interface PosterPreviewProps {
  currentPoster: string | null
  posters: Poster[]
  loading: boolean
  onDelete: (filename: string) => void
}

export default function PosterPreview({ currentPoster, posters, loading, onDelete }: PosterPreviewProps) {
  const { t } = useTranslation()
  const [selectedPoster, setSelectedPoster] = useState<string | null>(null)

  // Update selected poster when new poster is generated
  useEffect(() => {
    if (currentPoster && currentPoster !== selectedPoster) {
      setSelectedPoster(currentPoster)
    }
  }, [currentPoster])

  const displayPoster = selectedPoster || currentPoster
  
  const handlePosterClick = (posterUrl: string) => {
    setSelectedPoster(posterUrl)
  }

  return (
    <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 shadow-2xl border border-white/20">
      <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
        <span className="text-3xl">🖼️</span>
        {t('preview.title')}
      </h2>

      {displayPoster && !loading ? (
        <div className="space-y-4">
          <div className="relative group">
            <img
              src={displayPoster}
              alt="Generated Poster"
              className="w-full rounded-lg shadow-2xl"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-end justify-between p-4">
              <div className="flex gap-2">
                <a
                  href={displayPoster}
                  download
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg font-medium transition-colors"
                >
                  {t('preview.download')}
                </a>
              </div>
            </div>
          </div>

          {posters.length > 0 && (
            <div className="mt-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-medium">{t('preview.gallery')}</h3>
                <span className="text-sm text-slate-400">{posters.length} {t('i18n.language') === 'zh' ? '张' : 'items'}</span>
              </div>
              <div className="grid grid-cols-3 sm:grid-cols-4 gap-3 max-h-64 overflow-y-auto pr-2 custom-scrollbar">
                {posters.slice(0, 20).map((poster) => (
                  <div
                    key={poster.filename}
                    className={`relative group cursor-pointer rounded-xl overflow-hidden transition-all duration-300 ${
                      selectedPoster === poster.url 
                        ? 'ring-2 ring-purple-500 ring-offset-2 ring-offset-slate-900 scale-105 shadow-lg shadow-purple-500/50' 
                        : 'hover:scale-105 hover:shadow-xl'
                    }`}
                    onClick={() => handlePosterClick(poster.url)}
                  >
                    <img
                      src={poster.url}
                      alt={poster.filename}
                      className="w-full aspect-[3/4] object-cover"
                    />
                    {/* Selected indicator */}
                    {selectedPoster === poster.url && (
                      <div className="absolute top-2 right-2 w-6 h-6 bg-purple-500 rounded-full flex items-center justify-center shadow-lg">
                        <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                    )}
                    {/* Delete button overlay */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end justify-center pb-3">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          if (confirm(t('i18n.language') === 'zh' ? '确定要删除这张海报吗？' : 'Delete this poster?')) {
                            onDelete(poster.filename)
                          }
                        }}
                        className="p-2 bg-red-600 hover:bg-red-700 rounded-full transition-all hover:scale-110 shadow-lg"
                        title={t('preview.delete')}
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : !loading ? (
        <div className="aspect-[3/4] bg-gradient-to-br from-slate-800/50 to-slate-900/50 rounded-xl border-2 border-dashed border-slate-700 flex items-center justify-center">
          <div className="text-center space-y-4 p-8">
            <div className="text-7xl mb-4 animate-bounce">🗺️</div>
            <p className="text-slate-300 text-lg font-medium">{t('preview.noPosters')}</p>
            <p className="text-slate-500 text-sm max-w-xs mx-auto">
              {t('i18n.language') === 'zh' 
                ? '选择城市和主题，然后点击生成按钮创建你的第一张海报'
                : 'Select a city and theme, then click generate to create your first poster'
              }
            </p>
          </div>
        </div>
      ) : null}
    </div>
  )
}