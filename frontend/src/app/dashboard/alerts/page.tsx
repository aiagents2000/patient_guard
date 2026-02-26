'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { AlertTriangle, Bell, CheckCircle, Eye, ShieldAlert, Beaker } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { fetchAlerts, markAlertRead, resolveAlert } from '@/lib/api'
import { formatDateTime, getSeverityColor } from '@/lib/utils'
import type { Alert } from '@/types'

const SEVERITY_FILTERS = ['Tutti', 'critical', 'high', 'medium', 'low'] as const
const STATUS_FILTERS = ['Tutti', 'Non letti', 'Letti', 'Risolti'] as const

const ALERT_TYPE_LABELS: Record<string, { label: string; icon: React.ElementType }> = {
  critical_vitals: { label: 'Parametri critici', icon: AlertTriangle },
  risk_increase: { label: 'Aumento rischio', icon: ShieldAlert },
  readmission_warning: { label: 'Rischio riospedalizzazione', icon: Bell },
  lab_critical: { label: 'Valori lab critici', icon: Beaker },
}

const SEVERITY_LABELS: Record<string, string> = {
  critical: 'Critico',
  high: 'Alto',
  medium: 'Medio',
  low: 'Basso',
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [severityFilter, setSeverityFilter] = useState<string>('Tutti')
  const [statusFilter, setStatusFilter] = useState<string>('Tutti')

  useEffect(() => {
    setLoading(true)
    const filters: Record<string, string | boolean> = {}
    if (severityFilter !== 'Tutti') filters.severity = severityFilter

    fetchAlerts(filters as { severity?: string; limit?: number })
      .then(setAlerts)
      .catch(() => setAlerts([]))
      .finally(() => setLoading(false))
  }, [severityFilter])

  const handleMarkRead = async (id: string) => {
    try {
      const updated = await markAlertRead(id)
      setAlerts((prev) => prev.map((a) => (a.id === id ? updated : a)))
    } catch {}
  }

  const handleResolve = async (id: string) => {
    try {
      const updated = await resolveAlert(id)
      setAlerts((prev) => prev.map((a) => (a.id === id ? updated : a)))
    } catch {}
  }

  // Client-side status filter
  const filtered = alerts.filter((a) => {
    if (statusFilter === 'Non letti') return !a.is_read
    if (statusFilter === 'Letti') return a.is_read && !a.is_resolved
    if (statusFilter === 'Risolti') return a.is_resolved
    return true
  })

  const unreadCount = alerts.filter((a) => !a.is_read).length
  const criticalCount = alerts.filter((a) => a.severity === 'critical' && !a.is_resolved).length

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-text-primary mb-1">Alert</h2>
        <p className="text-sm text-text-muted">
          Gestione notifiche e alert clinici
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <Card className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-risk-critico/10">
            <AlertTriangle className="h-4 w-4 text-risk-critico" />
          </div>
          <div>
            <p className="text-xl font-bold font-display text-text-primary">{criticalCount}</p>
            <p className="text-[10px] sm:text-xs text-text-muted">Critici attivi</p>
          </div>
        </Card>
        <Card className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent/10">
            <Bell className="h-4 w-4 text-accent" />
          </div>
          <div>
            <p className="text-xl font-bold font-display text-text-primary">{unreadCount}</p>
            <p className="text-[10px] sm:text-xs text-text-muted">Non letti</p>
          </div>
        </Card>
        <Card className="hidden sm:flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-risk-basso/10">
            <CheckCircle className="h-4 w-4 text-risk-basso" />
          </div>
          <div>
            <p className="text-xl font-bold font-display text-text-primary">
              {alerts.filter((a) => a.is_resolved).length}
            </p>
            <p className="text-xs text-text-muted">Risolti</p>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <div className="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-3 p-4 border-b border-border">
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="h-9 px-3 rounded-lg bg-elevated border border-border text-sm text-text-secondary cursor-pointer focus:outline-none focus:ring-2 focus:ring-accent"
          >
            {SEVERITY_FILTERS.map((s) => (
              <option key={s} value={s}>
                {s === 'Tutti' ? 'Tutte le severità' : SEVERITY_LABELS[s] || s}
              </option>
            ))}
          </select>
          <div className="flex gap-2">
            {STATUS_FILTERS.map((s) => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                className={`h-9 px-3 rounded-lg text-sm font-medium transition-colors ${
                  statusFilter === s
                    ? 'bg-accent text-white'
                    : 'bg-elevated text-text-muted hover:text-text-secondary'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* Alert list */}
        <div className="divide-y divide-border">
          {loading ? (
            [...Array(5)].map((_, i) => (
              <div key={i} className="px-4 py-4">
                <div className="h-5 bg-elevated rounded animate-pulse" />
              </div>
            ))
          ) : filtered.length === 0 ? (
            <div className="px-4 py-12 text-center text-sm text-text-muted">
              Nessun alert trovato
            </div>
          ) : (
            filtered.map((alert) => {
              const typeInfo = ALERT_TYPE_LABELS[alert.alert_type] || {
                label: alert.alert_type,
                icon: Bell,
              }
              const TypeIcon = typeInfo.icon

              return (
                <div
                  key={alert.id}
                  className={`flex flex-col sm:flex-row sm:items-center gap-3 px-4 py-4 ${
                    !alert.is_read ? 'bg-elevated/40' : ''
                  } ${alert.is_resolved ? 'opacity-60' : ''}`}
                >
                  {/* Severity dot + icon */}
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <div
                      className="h-3 w-3 rounded-full shrink-0"
                      style={{ backgroundColor: getSeverityColor(alert.severity) }}
                    />
                    <TypeIcon className="h-4 w-4 shrink-0 text-text-muted" />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Link
                          href={`/dashboard/patient/${alert.patient_id}`}
                          className="text-sm font-medium text-text-primary hover:text-accent truncate"
                        >
                          {alert.patient_name}
                        </Link>
                        <Badge
                          variant={
                            alert.severity === 'critical'
                              ? 'risk-critico'
                              : alert.severity === 'high'
                              ? 'risk-alto'
                              : alert.severity === 'medium'
                              ? 'risk-medio'
                              : 'risk-basso'
                          }
                          className="text-[10px]"
                        >
                          {SEVERITY_LABELS[alert.severity] || alert.severity}
                        </Badge>
                        <span className="text-[10px] text-text-muted">{typeInfo.label}</span>
                      </div>
                      <p className="text-xs text-text-muted mt-1 line-clamp-2">{alert.message}</p>
                      {alert.created_at && (
                        <p className="text-[10px] text-text-muted mt-1">
                          {formatDateTime(alert.created_at)}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 shrink-0 self-end sm:self-auto">
                    {!alert.is_read && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleMarkRead(alert.id)}
                        title="Segna come letto"
                      >
                        <Eye className="h-3.5 w-3.5" />
                      </Button>
                    )}
                    {!alert.is_resolved && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleResolve(alert.id)}
                      >
                        <CheckCircle className="h-3.5 w-3.5 mr-1" />
                        Risolvi
                      </Button>
                    )}
                    {alert.is_resolved && (
                      <span className="text-xs text-risk-basso font-medium">Risolto</span>
                    )}
                  </div>
                </div>
              )
            })
          )}
        </div>
      </Card>
    </div>
  )
}
