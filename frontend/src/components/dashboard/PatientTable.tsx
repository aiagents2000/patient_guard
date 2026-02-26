'use client'

import Link from 'next/link'
import { ArrowUpDown, ChevronRight, Search } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { fetchPatients } from '@/lib/api'
import { getRiskColor } from '@/lib/utils'
import type { PatientSummaryItem, RiskLevel } from '@/types'

const DEPARTMENTS = [
  'Tutti',
  'Medicina Interna',
  'Cardiologia',
  'Pneumologia',
  'Nefrologia',
  'Geriatria',
]

const RISK_LEVELS = ['Tutti', 'critico', 'alto', 'medio', 'basso']

export default function PatientTable() {
  const [patients, setPatients] = useState<PatientSummaryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [deptFilter, setDeptFilter] = useState('Tutti')
  const [riskFilter, setRiskFilter] = useState('Tutti')
  const [sortBy, setSortBy] = useState<'risk_score' | 'name'>('risk_score')
  const [sortDesc, setSortDesc] = useState(true)

  useEffect(() => {
    setLoading(true)
    const filters: Record<string, string> = {}
    if (search) filters.search = search
    if (deptFilter !== 'Tutti') filters.department = deptFilter
    if (riskFilter !== 'Tutti') filters.risk_level = riskFilter

    fetchPatients(filters)
      .then(setPatients)
      .catch(() => setPatients([]))
      .finally(() => setLoading(false))
  }, [search, deptFilter, riskFilter])

  const sorted = [...patients].sort((a, b) => {
    if (sortBy === 'risk_score') {
      return sortDesc ? b.risk_score - a.risk_score : a.risk_score - b.risk_score
    }
    return sortDesc ? b.name.localeCompare(a.name) : a.name.localeCompare(b.name)
  })

  const toggleSort = (col: 'risk_score' | 'name') => {
    if (sortBy === col) setSortDesc(!sortDesc)
    else {
      setSortBy(col)
      setSortDesc(true)
    }
  }

  const riskBadgeVariant = (level: RiskLevel) =>
    `risk-${level}` as 'risk-basso' | 'risk-medio' | 'risk-alto' | 'risk-critico'

  return (
    <Card className="mt-6">
      {/* Filtri */}
      <div className="flex flex-wrap items-center gap-3 p-4 border-b border-border">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
          <input
            type="text"
            placeholder="Cerca paziente..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full h-9 pl-9 pr-3 rounded-lg bg-elevated border border-border text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent"
          />
        </div>
        <select
          value={deptFilter}
          onChange={(e) => setDeptFilter(e.target.value)}
          className="h-9 px-3 rounded-lg bg-elevated border border-border text-sm text-text-secondary cursor-pointer focus:outline-none focus:ring-2 focus:ring-accent"
        >
          {DEPARTMENTS.map((d) => (
            <option key={d} value={d}>{d === 'Tutti' ? 'Tutti i reparti' : d}</option>
          ))}
        </select>
        <select
          value={riskFilter}
          onChange={(e) => setRiskFilter(e.target.value)}
          className="h-9 px-3 rounded-lg bg-elevated border border-border text-sm text-text-secondary cursor-pointer focus:outline-none focus:ring-2 focus:ring-accent"
        >
          {RISK_LEVELS.map((r) => (
            <option key={r} value={r}>
              {r === 'Tutti' ? 'Tutti i livelli' : r.charAt(0).toUpperCase() + r.slice(1)}
            </option>
          ))}
        </select>
      </div>

      {/* Tabella */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border text-xs text-text-muted uppercase tracking-wider">
              <th className="px-4 py-3 text-left w-20">
                <button onClick={() => toggleSort('risk_score')} className="flex items-center gap-1 hover:text-text-secondary">
                  Score <ArrowUpDown className="h-3 w-3" />
                </button>
              </th>
              <th className="px-4 py-3 text-left">
                <button onClick={() => toggleSort('name')} className="flex items-center gap-1 hover:text-text-secondary">
                  Paziente <ArrowUpDown className="h-3 w-3" />
                </button>
              </th>
              <th className="px-4 py-3 text-left">Rischio</th>
              <th className="px-4 py-3 text-left">Reparto</th>
              <th className="px-4 py-3 text-left">Riosped.</th>
              <th className="px-4 py-3 text-right w-24">Azione</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              [...Array(5)].map((_, i) => (
                <tr key={i} className="border-b border-border/50">
                  <td colSpan={6} className="px-4 py-4">
                    <div className="h-4 bg-elevated rounded animate-pulse" />
                  </td>
                </tr>
              ))
            ) : sorted.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-12 text-center text-text-muted text-sm">
                  Nessun paziente trovato
                </td>
              </tr>
            ) : (
              sorted.map((p) => (
                <tr
                  key={p.id}
                  className="border-b border-border/50 hover:bg-elevated/50 transition-colors"
                >
                  <td className="px-4 py-3">
                    <span
                      className="inline-flex h-8 w-12 items-center justify-center rounded-md font-display text-sm font-bold"
                      style={{
                        backgroundColor: getRiskColor(p.risk_score) + '20',
                        color: getRiskColor(p.risk_score),
                      }}
                    >
                      {p.risk_score}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div>
                      <p className="text-sm font-medium text-text-primary">{p.name}</p>
                      <p className="text-xs text-text-muted">
                        {p.age} anni, {p.gender}
                      </p>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={riskBadgeVariant(p.risk_level)}>
                      {p.risk_level.charAt(0).toUpperCase() + p.risk_level.slice(1)}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-sm text-text-secondary">{p.department}</td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-text-muted">
                      {(p.readmission_probability * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link href={`/dashboard/patient/${p.id}`}>
                      <Button variant="ghost" size="sm">
                        Dettagli <ChevronRight className="ml-1 h-3 w-3" />
                      </Button>
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </Card>
  )
}
