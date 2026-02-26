'use client'

import { useEffect, useState } from 'react'
import AlertBanner from '@/components/dashboard/AlertBanner'
import DepartmentChart from '@/components/dashboard/DepartmentChart'
import PatientTable from '@/components/dashboard/PatientTable'
import RiskDistributionChart from '@/components/dashboard/RiskDistributionChart'
import StatsRow from '@/components/dashboard/StatsRow'
import { fetchStatsDepartment, fetchStatsOverview } from '@/lib/api'
import type { DepartmentStats, StatsOverview } from '@/types'

export default function DashboardPage() {
  const [stats, setStats] = useState<StatsOverview | null>(null)
  const [departments, setDepartments] = useState<DepartmentStats[] | null>(null)

  useEffect(() => {
    fetchStatsOverview().then(setStats).catch(() => {})
    fetchStatsDepartment().then(setDepartments).catch(() => {})
  }, [])

  return (
    <div className="space-y-6">
      <AlertBanner />

      <div>
        <h2 className="text-xl font-bold text-text-primary mb-1">Dashboard</h2>
        <p className="text-sm text-text-muted">
          Panoramica pazienti e predizioni AI in tempo reale
        </p>
      </div>

      <StatsRow stats={stats} />

      <div className="grid grid-cols-2 gap-4">
        <RiskDistributionChart distribution={stats?.risk_distribution ?? null} />
        <DepartmentChart departments={departments} />
      </div>

      <div>
        <h3 className="text-base font-semibold text-text-primary mb-3">Lista Pazienti</h3>
        <PatientTable />
      </div>
    </div>
  )
}
