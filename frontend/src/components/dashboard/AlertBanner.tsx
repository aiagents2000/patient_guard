'use client'

import { AlertTriangle, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { fetchAlerts } from '@/lib/api'

export default function AlertBanner() {
  const [criticalCount, setCriticalCount] = useState(0)
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    fetchAlerts({ severity: 'critical', is_read: false, limit: 50 })
      .then((alerts) => setCriticalCount(alerts.length))
      .catch(() => {})
  }, [])

  if (dismissed || criticalCount === 0) return null

  return (
    <div className="flex items-center justify-between bg-risk-critico/10 border border-risk-critico/30 rounded-lg px-4 py-2.5 mx-6 mt-4">
      <div className="flex items-center gap-2">
        <AlertTriangle className="h-4 w-4 text-risk-critico" />
        <span className="text-sm font-medium text-risk-critico">
          {criticalCount} alert critici attivi — Verifica immediatamente
        </span>
      </div>
      <button
        onClick={() => setDismissed(true)}
        className="text-risk-critico/60 hover:text-risk-critico transition-colors"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}
