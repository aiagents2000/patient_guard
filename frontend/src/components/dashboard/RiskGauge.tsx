'use client'

import { getChartTheme, getRiskColor } from '@/lib/utils'
import { useTheme } from '@/components/ThemeProvider'

interface Props {
  score: number
  size?: number
}

export default function RiskGauge({ score, size = 160 }: Props) {
  useTheme() // re-render on theme change
  const ct = getChartTheme()
  const color = getRiskColor(score)
  const r = (size - 20) / 2
  const cx = size / 2
  const cy = size / 2
  const circumference = Math.PI * r // semicircle
  const progress = (score / 100) * circumference

  return (
    <div className="relative inline-flex flex-col items-center">
      <svg width={size} height={size / 2 + 20} viewBox={`0 0 ${size} ${size / 2 + 20}`}>
        {/* Track */}
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke={ct.gaugeBg}
          strokeWidth="10"
          strokeLinecap="round"
        />
        {/* Progress */}
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={`${circumference}`}
          strokeDashoffset={`${circumference - progress}`}
          style={{ transition: 'stroke-dashoffset 1s ease' }}
        />
      </svg>
      {/* Score al centro */}
      <div className="absolute inset-0 flex flex-col items-center justify-end pb-2">
        <span className="font-display text-4xl font-bold" style={{ color }}>
          {score}
        </span>
        <span className="text-xs text-text-muted">/100</span>
      </div>
    </div>
  )
}
