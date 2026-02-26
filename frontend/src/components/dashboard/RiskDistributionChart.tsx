'use client'

import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { getChartTheme } from '@/lib/utils'
import { useTheme } from '@/components/ThemeProvider'
import type { RiskDistribution } from '@/types'

interface Props {
  distribution: RiskDistribution | null
}

const COLORS = {
  Basso: '#10b981',
  Medio: '#f59e0b',
  Alto: '#f97316',
  Critico: '#ef4444',
}

export default function RiskDistributionChart({ distribution }: Props) {
  useTheme() // re-render on theme change
  const ct = getChartTheme()

  if (!distribution) return <Card className="h-72 animate-pulse" />

  const data = [
    { name: 'Basso', value: distribution.basso },
    { name: 'Medio', value: distribution.medio },
    { name: 'Alto', value: distribution.alto },
    { name: 'Critico', value: distribution.critico },
  ].filter((d) => d.value > 0)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Distribuzione Rischio</CardTitle>
      </CardHeader>
      <CardContent className="h-60">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={85}
              dataKey="value"
              strokeWidth={0}
            >
              {data.map((entry) => (
                <Cell
                  key={entry.name}
                  fill={COLORS[entry.name as keyof typeof COLORS]}
                />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: ct.tooltipBg,
                border: `1px solid ${ct.tooltipBorder}`,
                borderRadius: '8px',
                fontSize: '12px',
              }}
            />
            <Legend
              formatter={(value) => (
                <span className="text-xs text-text-secondary">{value}</span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
