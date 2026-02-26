'use client'

import { Activity, AlertTriangle, TrendingUp, Users } from 'lucide-react'
import { Card } from '@/components/ui/card'
import type { StatsOverview } from '@/types'

interface StatsRowProps {
  stats: StatsOverview | null
}

export default function StatsRow({ stats }: StatsRowProps) {
  if (!stats) {
    return (
      <div className="grid grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="animate-pulse h-24" />
        ))}
      </div>
    )
  }

  const highRisk =
    (stats.risk_distribution.alto || 0) + (stats.risk_distribution.critico || 0)

  const items = [
    {
      label: 'Pazienti monitorati',
      value: stats.total_patients,
      icon: Users,
      color: 'text-accent',
      bg: 'bg-accent/10',
    },
    {
      label: 'Rischio alto/critico',
      value: highRisk,
      icon: AlertTriangle,
      color: 'text-risk-critico',
      bg: 'bg-risk-critico/10',
    },
    {
      label: 'Score medio',
      value: stats.avg_risk_score.toFixed(1),
      icon: Activity,
      color: 'text-risk-medio',
      bg: 'bg-risk-medio/10',
    },
    {
      label: 'Alert attivi',
      value: stats.active_alerts,
      icon: TrendingUp,
      color: 'text-risk-alto',
      bg: 'bg-risk-alto/10',
    },
  ]

  return (
    <div className="grid grid-cols-4 gap-4">
      {items.map((item) => {
        const Icon = item.icon
        return (
          <Card key={item.label} className="flex items-center gap-4">
            <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${item.bg}`}>
              <Icon className={`h-5 w-5 ${item.color}`} />
            </div>
            <div>
              <p className="text-2xl font-bold font-display text-text-primary">{item.value}</p>
              <p className="text-xs text-text-muted">{item.label}</p>
            </div>
          </Card>
        )
      })}
    </div>
  )
}
