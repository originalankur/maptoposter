import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'

interface ProgressBarProps {
  isGenerating: boolean
}

const steps = [
  { key: 'coordinates', duration: 2000 },
  { key: 'downloading', duration: 15000 },
  { key: 'rendering', duration: 20000 },
  { key: 'finalizing', duration: 5000 }
]

export default function ProgressBar({ isGenerating }: ProgressBarProps) {
  const { t } = useTranslation()
  const [currentStep, setCurrentStep] = useState(0)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    if (!isGenerating) {
      setCurrentStep(0)
      setProgress(0)
      return
    }

    let currentTime = 0
    const totalDuration = steps.reduce((sum, step) => sum + step.duration, 0)

    const timer = setInterval(() => {
      currentTime += 100

      // Calculate which step we're on
      let accumulatedTime = 0
      let stepIndex = 0
      for (let i = 0; i < steps.length; i++) {
        if (currentTime >= accumulatedTime && currentTime < accumulatedTime + steps[i].duration) {
          stepIndex = i
          break
        }
        accumulatedTime += steps[i].duration
        if (i === steps.length - 1) stepIndex = i
      }

      setCurrentStep(stepIndex)
      setProgress(Math.min((currentTime / totalDuration) * 100, 95))

      if (currentTime >= totalDuration) {
        clearInterval(timer)
      }
    }, 100)

    return () => clearInterval(timer)
  }, [isGenerating])

  if (!isGenerating) return null

  const stepLabels: Record<string, { en: string; zh: string }> = {
    coordinates: { en: 'Looking up coordinates...', zh: '查找坐标中...' },
    downloading: { en: 'Downloading map data...', zh: '下载地图数据中...' },
    rendering: { en: 'Rendering your poster...', zh: '渲染海报中...' },
    finalizing: { en: 'Finalizing...', zh: '最后处理中...' }
  }

  const currentStepKey = steps[currentStep].key
  const currentLabel = stepLabels[currentStepKey]

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-8 max-w-md w-full shadow-2xl border border-white/10">
        {/* Title */}
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full mx-auto mb-4 flex items-center justify-center">
            <svg className="w-8 h-8 text-white animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-white mb-2">
            {t('i18n.language') === 'zh' ? '正在生成您的海报...' : 'Generating Your Poster...'}
          </h3>
          <p className="text-slate-400 text-sm">
            {t('i18n.language') === 'zh' 
              ? '这可能需要 30-60 秒，请耐心等待'
              : 'This may take 30-60 seconds, please wait'
            }
          </p>
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex justify-between text-sm text-slate-400 mb-2">
            <span>{Math.round(progress)}%</span>
            <span>{currentStep + 1} / {steps.length}</span>
          </div>
          <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-purple-500 via-pink-500 to-indigo-500 transition-all duration-300 ease-out relative"
              style={{ width: `${progress}%` }}
            >
              <div className="absolute inset-0 bg-white/20 animate-pulse" />
            </div>
          </div>
        </div>

        {/* Steps */}
        <div className="space-y-3">
          {steps.map((step, index) => (
            <div 
              key={step.key}
              className={`flex items-center gap-3 transition-all duration-300 ${
                index === currentStep 
                  ? 'text-white scale-105' 
                  : index < currentStep 
                    ? 'text-green-400' 
                    : 'text-slate-500'
              }`}
            >
              {/* Icon */}
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                index === currentStep 
                  ? 'bg-gradient-to-br from-purple-500 to-pink-500 animate-pulse' 
                  : index < currentStep 
                    ? 'bg-green-500' 
                    : 'bg-slate-700'
              }`}>
                {index < currentStep ? (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : index === currentStep ? (
                  <div className="w-3 h-3 bg-white rounded-full animate-ping" />
                ) : (
                  <div className="w-2 h-2 bg-slate-500 rounded-full" />
                )}
              </div>

              {/* Label */}
              <span className="text-sm font-medium">
                {t('i18n.language') === 'zh' ? currentLabel.zh : currentLabel.en}
              </span>
            </div>
          ))}
        </div>

        {/* Fun fact */}
        <div className="mt-6 p-4 bg-slate-800/50 rounded-lg border border-slate-700">
          <p className="text-xs text-slate-400 text-center">
            {t('i18n.language') === 'zh' 
              ? '💡 提示：生成的地图使用 OpenStreetMap 数据，覆盖全球！'
              : '💡 Tip: Maps are generated using OpenStreetMap data!'
            }
          </p>
        </div>
      </div>
    </div>
  )
}
