'use client'

import { useEffect, useState } from 'react'
import MyAppointments from '@/components/patient-portal/MyAppointments'
import MyLabResults from '@/components/patient-portal/MyLabResults'
import MyMedications from '@/components/patient-portal/MyMedications'
import MyVitals from '@/components/patient-portal/MyVitals'
import PatientOverview from '@/components/patient-portal/PatientOverview'
import { fetchPatientDetail, fetchPatients } from '@/lib/api'
import type { PatientDetail } from '@/types'

export default function PatientPortalPage() {
  const [patient, setPatient] = useState<PatientDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    // In produzione: usare auth per determinare il paziente loggato.
    // Per la demo: carichiamo il primo paziente dalla lista.
    async function loadPatient() {
      try {
        const patients = await fetchPatients({ limit: 1 })
        if (patients.length > 0) {
          const detail = await fetchPatientDetail(patients[0].id)
          setPatient(detail)
        }
      } catch {
        setError(true)
      } finally {
        setLoading(false)
      }
    }
    loadPatient()
  }, [])

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-gray-200 rounded animate-pulse" />
        <div className="h-32 bg-gray-100 rounded-xl animate-pulse" />
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-28 bg-gray-100 rounded-xl animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (error || !patient) {
    return (
      <div className="text-center py-20">
        <p className="text-lg text-gray-500">
          Non riusciamo a caricare i tuoi dati.
        </p>
        <p className="text-base text-gray-400 mt-2">
          Verifica che il servizio sia attivo e riprova.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <PatientOverview
        name={patient.name}
        age={patient.age}
        department={patient.department}
        prediction={patient.prediction}
      />

      <MyVitals vitals={patient.vitals} />

      <MyMedications medications={patient.medications} />

      <MyLabResults vitals={patient.vitals} />

      <MyAppointments department={patient.department} />
    </div>
  )
}
