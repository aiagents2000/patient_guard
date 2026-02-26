'use client'

import { CalendarDays, Clock } from 'lucide-react'

interface Props {
  department: string
}

export default function MyAppointments({ department }: Props) {
  // Appuntamenti demo — in produzione verrebbero dal backend
  const now = new Date()

  const appointments = [
    {
      type: 'Visita di controllo',
      department: department,
      date: new Date(now.getTime() + 3 * 24 * 60 * 60 * 1000),
      time: '09:30',
      doctor: 'Dott. Rossi',
    },
    {
      type: 'Esami del sangue',
      department: 'Laboratorio Analisi',
      date: new Date(now.getTime() + 5 * 24 * 60 * 60 * 1000),
      time: '07:30',
      doctor: '',
    },
    {
      type: 'Controllo post-dimissione',
      department: 'Ambulatorio',
      date: new Date(now.getTime() + 14 * 24 * 60 * 60 * 1000),
      time: '10:00',
      doctor: 'Dott. Bianchi',
    },
  ]

  return (
    <section>
      <h3 className="text-xl font-bold text-gray-900 mb-4">I miei appuntamenti</h3>
      <div className="space-y-3">
        {appointments.map((apt, i) => (
          <div
            key={i}
            className="flex items-center gap-4 rounded-xl border-2 border-gray-200 bg-gray-50 p-4"
          >
            <div className="flex h-12 w-12 flex-shrink-0 flex-col items-center justify-center rounded-xl bg-indigo-100 text-indigo-700">
              <span className="text-lg font-bold leading-none">
                {apt.date.getDate()}
              </span>
              <span className="text-[10px] font-medium uppercase">
                {apt.date.toLocaleDateString('it-IT', { month: 'short' })}
              </span>
            </div>
            <div className="flex-1">
              <p className="text-base font-semibold text-gray-900">{apt.type}</p>
              <div className="flex flex-wrap items-center gap-3 mt-1 text-sm text-gray-600">
                <span className="flex items-center gap-1">
                  <CalendarDays className="h-3.5 w-3.5" />
                  {apt.date.toLocaleDateString('it-IT', {
                    weekday: 'long',
                    day: 'numeric',
                    month: 'long',
                  })}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3.5 w-3.5" />
                  ore {apt.time}
                </span>
              </div>
              <p className="text-sm text-gray-500 mt-0.5">
                {apt.department}
                {apt.doctor && ` — ${apt.doctor}`}
              </p>
            </div>
          </div>
        ))}
      </div>
      <p className="mt-4 text-sm text-gray-500">
        Se non puoi presentarti a un appuntamento, avvisa il reparto con anticipo.
      </p>
    </section>
  )
}
