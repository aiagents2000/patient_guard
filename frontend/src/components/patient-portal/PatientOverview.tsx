'use client'

import { Heart, ShieldCheck, AlertTriangle } from 'lucide-react'
import type { Prediction } from '@/types'

interface Props {
  name: string
  age: number
  department: string
  prediction: Prediction
}

// Traduce il rischio in linguaggio paziente-friendly
function getStatusConfig(riskLevel: string) {
  switch (riskLevel) {
    case 'basso':
      return {
        color: 'bg-green-500',
        bgLight: 'bg-green-50 border-green-200',
        textColor: 'text-green-700',
        icon: ShieldCheck,
        label: 'Buono',
        message:
          'Il tuo stato di salute è nella norma. Continua a seguire le indicazioni del tuo medico e la terapia prescritta.',
      }
    case 'medio':
      return {
        color: 'bg-yellow-500',
        bgLight: 'bg-yellow-50 border-yellow-200',
        textColor: 'text-yellow-700',
        icon: AlertTriangle,
        label: 'Da monitorare',
        message:
          'Alcuni parametri richiedono attenzione. Il tuo medico sta monitorando la situazione. Segui con cura la terapia prescritta.',
      }
    case 'alto':
    case 'critico':
      return {
        color: 'bg-red-500',
        bgLight: 'bg-red-50 border-red-200',
        textColor: 'text-red-700',
        icon: Heart,
        label: 'Attenzione',
        message:
          'Il tuo stato richiede attenzione medica. Il personale sanitario è al corrente e sta seguendo la tua situazione con la massima cura.',
      }
    default:
      return {
        color: 'bg-gray-400',
        bgLight: 'bg-gray-50 border-gray-200',
        textColor: 'text-gray-600',
        icon: ShieldCheck,
        label: '—',
        message: '',
      }
  }
}

export default function PatientOverview({ name, age, department, prediction }: Props) {
  const status = getStatusConfig(prediction.risk_level)
  const Icon = status.icon

  return (
    <section className="space-y-4">
      {/* Saluto */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">
          Ciao, {name.split(' ')[0]}
        </h2>
        <p className="text-base text-gray-500">
          {age} anni — Reparto: {department}
        </p>
      </div>

      {/* Semaforo stato */}
      <div className={`rounded-2xl border-2 p-6 ${status.bgLight}`}>
        <div className="flex items-center gap-4">
          {/* Cerchio semaforo */}
          <div className={`flex h-16 w-16 flex-shrink-0 items-center justify-center rounded-full ${status.color}`}>
            <Icon className="h-8 w-8 text-white" />
          </div>
          <div>
            <h3 className={`text-xl font-bold ${status.textColor}`}>
              Il tuo stato: {status.label}
            </h3>
            <p className="mt-1 text-base text-gray-700 leading-relaxed">
              {status.message}
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
