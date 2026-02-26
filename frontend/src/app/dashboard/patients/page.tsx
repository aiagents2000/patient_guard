'use client'

import PatientTable from '@/components/dashboard/PatientTable'

export default function PatientsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-text-primary mb-1">Pazienti</h2>
        <p className="text-sm text-text-muted">
          Registro completo dei pazienti monitorati
        </p>
      </div>

      <PatientTable />
    </div>
  )
}
