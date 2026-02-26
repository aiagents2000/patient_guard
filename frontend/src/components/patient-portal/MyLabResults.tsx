'use client'

import { FlaskConical } from 'lucide-react'
import type { Vitals } from '@/types'

interface Props {
  vitals: Vitals
}

interface LabItem {
  name: string
  value: string
  explanation: string
  status: 'normal' | 'monitor' | 'attention'
}

function getLabItems(vitals: Vitals): LabItem[] {
  const items: LabItem[] = []

  // Creatinina
  const creat = vitals.creatinine
  if (creat <= 1.2) {
    items.push({ name: 'Funzione renale (creatinina)', value: `${creat.toFixed(2)} mg/dL`, explanation: 'I tuoi reni funzionano bene.', status: 'normal' })
  } else if (creat <= 2.0) {
    items.push({ name: 'Funzione renale (creatinina)', value: `${creat.toFixed(2)} mg/dL`, explanation: 'I reni hanno bisogno di un po\' di attenzione. Il medico monitora la situazione.', status: 'monitor' })
  } else {
    items.push({ name: 'Funzione renale (creatinina)', value: `${creat.toFixed(2)} mg/dL`, explanation: 'I reni hanno bisogno di cure. Il team medico sta intervenendo.', status: 'attention' })
  }

  // Emoglobina
  const hb = vitals.hemoglobin
  if (hb >= 12.0) {
    items.push({ name: 'Emoglobina (sangue)', value: `${hb.toFixed(1)} g/dL`, explanation: 'Il tuo livello di emoglobina è nella norma.', status: 'normal' })
  } else if (hb >= 10.0) {
    items.push({ name: 'Emoglobina (sangue)', value: `${hb.toFixed(1)} g/dL`, explanation: 'Il livello è un po\' basso. Il medico potrebbe prescrivere integratori di ferro.', status: 'monitor' })
  } else {
    items.push({ name: 'Emoglobina (sangue)', value: `${hb.toFixed(1)} g/dL`, explanation: 'Livello basso — il team medico sta valutando il trattamento migliore.', status: 'attention' })
  }

  // SpO2
  const spo2 = vitals.spo2
  if (spo2 >= 95) {
    items.push({ name: 'Ossigeno nel sangue (SpO2)', value: `${spo2.toFixed(1)}%`, explanation: 'L\'ossigeno nel tuo sangue è a un buon livello.', status: 'normal' })
  } else if (spo2 >= 92) {
    items.push({ name: 'Ossigeno nel sangue (SpO2)', value: `${spo2.toFixed(1)}%`, explanation: 'Un po\' sotto la norma. Potrebbe essere necessario ossigeno supplementare.', status: 'monitor' })
  } else {
    items.push({ name: 'Ossigeno nel sangue (SpO2)', value: `${spo2.toFixed(1)}%`, explanation: 'Livello basso di ossigeno. Il personale sta monitorando attentamente.', status: 'attention' })
  }

  return items
}

const statusStyles = {
  normal: { bg: 'bg-green-50 border-green-200', dot: 'bg-green-500' },
  monitor: { bg: 'bg-yellow-50 border-yellow-200', dot: 'bg-yellow-500' },
  attention: { bg: 'bg-red-50 border-red-200', dot: 'bg-red-500' },
}

export default function MyLabResults({ vitals }: Props) {
  const labs = getLabItems(vitals)

  return (
    <section>
      <h3 className="text-xl font-bold text-gray-900 mb-4">I miei esami</h3>
      <div className="space-y-3">
        {labs.map((lab, i) => {
          const style = statusStyles[lab.status]
          return (
            <div
              key={i}
              className={`rounded-xl border-2 p-4 ${style.bg}`}
            >
              <div className="flex items-start gap-3">
                <FlaskConical className="h-5 w-5 mt-0.5 text-gray-500 flex-shrink-0" />
                <div>
                  <div className="flex items-center gap-2">
                    <p className="text-base font-semibold text-gray-900">{lab.name}</p>
                    <span className={`h-2.5 w-2.5 rounded-full ${style.dot}`} />
                  </div>
                  <p className="text-lg font-bold font-mono text-gray-900 mt-1">{lab.value}</p>
                  <p className="text-sm text-gray-600 mt-1">{lab.explanation}</p>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
