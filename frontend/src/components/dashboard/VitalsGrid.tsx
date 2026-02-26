'use client'

import { Card } from '@/components/ui/card'
import { getVitalLabel, getVitalUnit, isVitalAbnormal } from '@/lib/utils'
import type { Vitals } from '@/types'

interface Props {
  vitals: Vitals
}

const VITAL_KEYS = [
  'systolic_bp',
  'diastolic_bp',
  'heart_rate',
  'spo2',
  'temperature',
  'glucose',
  'creatinine',
  'hemoglobin',
] as const

export default function VitalsGrid({ vitals }: Props) {
  return (
    <div className="grid grid-cols-4 gap-3">
      {VITAL_KEYS.map((key) => {
        const value = vitals[key as keyof Vitals]
        const numValue = typeof value === 'number' ? value : 0
        const abnormal = isVitalAbnormal(key, numValue)

        return (
          <Card
            key={key}
            className={`p-3 ${
              abnormal ? 'border-risk-critico/40 bg-risk-critico/5' : ''
            }`}
          >
            <p className="text-[11px] text-text-muted mb-1">{getVitalLabel(key)}</p>
            <p
              className={`font-display text-lg font-bold ${
                abnormal ? 'text-risk-critico' : 'text-text-primary'
              }`}
            >
              {typeof numValue === 'number' && numValue % 1 !== 0
                ? numValue.toFixed(1)
                : numValue}
            </p>
            <p className="text-[10px] text-text-muted">
              {getVitalUnit(key)}
              {abnormal && (
                <span className="ml-1 text-risk-critico font-medium">Anomalo</span>
              )}
            </p>
          </Card>
        )
      })}
    </div>
  )
}
