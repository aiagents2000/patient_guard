'use client'

import {
  Activity,
  Droplets,
  Heart,
  Thermometer,
} from 'lucide-react'
import type { Vitals } from '@/types'

interface Props {
  vitals: Vitals
}

interface VitalCardProps {
  icon: React.ElementType
  label: string
  value: string
  status: 'normal' | 'monitor' | 'attention'
  statusText: string
}

function getVitalStatus(key: string, value: number): { status: 'normal' | 'monitor' | 'attention'; text: string } {
  switch (key) {
    case 'systolic_bp':
      if (value >= 90 && value <= 140) return { status: 'normal', text: 'Nella norma' }
      if (value > 140 && value <= 160) return { status: 'monitor', text: 'Leggermente alta' }
      if (value < 90) return { status: 'attention', text: 'Bassa, parlane col medico' }
      return { status: 'attention', text: 'Alta, parlane col medico' }

    case 'heart_rate':
      if (value >= 60 && value <= 100) return { status: 'normal', text: 'Nella norma' }
      if (value > 100 && value <= 110) return { status: 'monitor', text: 'Un po\' accelerato' }
      return { status: 'attention', text: 'Da monitorare' }

    case 'temperature':
      if (value >= 36.0 && value <= 37.5) return { status: 'normal', text: 'Nella norma' }
      if (value > 37.5 && value <= 38.0) return { status: 'monitor', text: 'Leggera febbre' }
      return { status: 'attention', text: 'Febbre, avvisa il medico' }

    case 'glucose':
      if (value >= 70 && value <= 140) return { status: 'normal', text: 'Nella norma' }
      if (value > 140 && value <= 200) return { status: 'monitor', text: 'Leggermente alta' }
      return { status: 'attention', text: 'Da monitorare' }

    default:
      return { status: 'normal', text: 'Nella norma' }
  }
}

const statusStyles = {
  normal: { bg: 'bg-green-50 border-green-200', text: 'text-green-700', dot: 'bg-green-500' },
  monitor: { bg: 'bg-yellow-50 border-yellow-200', text: 'text-yellow-700', dot: 'bg-yellow-500' },
  attention: { bg: 'bg-red-50 border-red-200', text: 'text-red-700', dot: 'bg-red-500' },
}

function VitalCard({ icon: Icon, label, value, status, statusText }: VitalCardProps) {
  const style = statusStyles[status]
  return (
    <div className={`rounded-xl border-2 p-4 ${style.bg}`}>
      <div className="flex items-center gap-3 mb-2">
        <Icon className="h-5 w-5 text-gray-500" />
        <span className="text-sm font-medium text-gray-600">{label}</span>
      </div>
      <p className="text-2xl font-bold text-gray-900 font-mono">{value}</p>
      <div className="flex items-center gap-2 mt-2">
        <span className={`h-2.5 w-2.5 rounded-full ${style.dot}`} />
        <span className={`text-sm font-medium ${style.text}`}>{statusText}</span>
      </div>
    </div>
  )
}

export default function MyVitals({ vitals }: Props) {
  const bp = getVitalStatus('systolic_bp', vitals.systolic_bp)
  const hr = getVitalStatus('heart_rate', vitals.heart_rate)
  const temp = getVitalStatus('temperature', vitals.temperature)
  const gluc = getVitalStatus('glucose', vitals.glucose)

  return (
    <section>
      <h3 className="text-xl font-bold text-gray-900 mb-4">I miei parametri</h3>
      <div className="grid grid-cols-2 gap-3">
        <VitalCard
          icon={Activity}
          label="Pressione arteriosa"
          value={`${vitals.systolic_bp}/${vitals.diastolic_bp}`}
          status={bp.status}
          statusText={bp.text}
        />
        <VitalCard
          icon={Heart}
          label="Battito cardiaco"
          value={`${vitals.heart_rate} bpm`}
          status={hr.status}
          statusText={hr.text}
        />
        <VitalCard
          icon={Thermometer}
          label="Temperatura"
          value={`${vitals.temperature.toFixed(1)}°C`}
          status={temp.status}
          statusText={temp.text}
        />
        <VitalCard
          icon={Droplets}
          label="Glicemia"
          value={`${vitals.glucose} mg/dL`}
          status={gluc.status}
          statusText={gluc.text}
        />
      </div>
    </section>
  )
}
