'use client'

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { getChartTheme } from '@/lib/utils'
import { useTheme } from '@/components/ThemeProvider'
import type { RiskFactor } from '@/types'

interface Props {
  factors: RiskFactor[]
}

const IMPACT_COLORS = {
  alto: '#ef4444',
  medio: '#f59e0b',
  basso: '#10b981',
}

export default function RiskFactorsChart({ factors }: Props) {
  useTheme() // re-render on theme change
  const ct = getChartTheme()

  if (!factors || factors.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle>Fattori di Rischio</CardTitle></CardHeader>
        <CardContent>
          <p className="text-sm text-text-muted">Nessun fattore disponibile</p>
        </CardContent>
      </Card>
    )
  }

  const data = factors.map((f) => ({
    name: f.factor.length > 25 ? f.factor.substring(0, 25) + '...' : f.factor,
    fullName: f.factor,
    contribution: f.contribution,
    impact: f.impact,
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle>Top 5 Fattori di Rischio</CardTitle>
      </CardHeader>
      <CardContent className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 0, right: 10, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} horizontal={false} />
            <XAxis type="number" tick={{ fill: ct.axis, fontSize: 10 }} axisLine={{ stroke: ct.grid }} />
            <YAxis
              type="category"
              dataKey="name"
              width={140}
              tick={{ fill: ct.axis, fontSize: 10 }}
              axisLine={{ stroke: ct.grid }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: ct.tooltipBg,
                border: `1px solid ${ct.tooltipBorder}`,
                borderRadius: '8px',
                fontSize: '12px',
              }}
              formatter={(value: number) => [value.toFixed(2), 'Contributo']}
              labelFormatter={(_, payload) => payload?.[0]?.payload?.fullName || ''}
            />
            <Bar dataKey="contribution" radius={[0, 4, 4, 0]}>
              {data.map((entry, index) => (
                <Cell
                  key={index}
                  fill={IMPACT_COLORS[entry.impact as keyof typeof IMPACT_COLORS] || '#6366f1'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
