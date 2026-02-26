'use client'

import { Pill } from 'lucide-react'
import type { Medication } from '@/types'

interface Props {
  medications: Medication[]
}

export default function MyMedications({ medications }: Props) {
  if (medications.length === 0) {
    return (
      <section>
        <h3 className="text-xl font-bold text-gray-900 mb-4">Le mie terapie</h3>
        <p className="text-base text-gray-500">Nessuna terapia in corso.</p>
      </section>
    )
  }

  return (
    <section>
      <h3 className="text-xl font-bold text-gray-900 mb-4">Le mie terapie</h3>
      <div className="space-y-3">
        {medications.map((med, i) => (
          <div
            key={i}
            className="flex items-center gap-4 rounded-xl border-2 border-indigo-100 bg-indigo-50/50 p-4"
          >
            <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-indigo-100">
              <Pill className="h-5 w-5 text-indigo-600" />
            </div>
            <div className="flex-1">
              <p className="text-base font-semibold text-gray-900">{med.name}</p>
              <p className="text-sm text-gray-600">
                {med.dosage && <span>{med.dosage}</span>}
                {med.dosage && med.frequency && <span> — </span>}
                {med.frequency && <span>{med.frequency}</span>}
              </p>
            </div>
          </div>
        ))}
      </div>
      <p className="mt-4 text-sm text-gray-500">
        Prendi i farmaci come indicato dal medico. Se hai dubbi su dosaggio o orari, chiedi al personale infermieristico.
      </p>
    </section>
  )
}
