'use client'

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { getChartTheme, getRiskColor } from '@/lib/utils'
import { useTheme } from '@/components/ThemeProvider'
import type { DepartmentStats } from '@/types'

interface Props {
  departments: DepartmentStats[] | null
}

export default function DepartmentChart({ departments }: Props) {
  useTheme() // re-render on theme change
  const ct = getChartTheme()

  if (!departments) return <Card className="h-72 animate-pulse" />

  const data = departments.map((d) => ({
    name: d.department.replace('Medicina Interna', 'Med. Int.'),
    score: d.avg_risk_score,
    count: d.patient_count,
    fullName: d.department,
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle>Score Medio per Reparto</CardTitle>
      </CardHeader>
      <CardContent className="h-60">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: -10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
            <XAxis
              dataKey="name"
              tick={{ fill: ct.axis, fontSize: 11 }}
              axisLine={{ stroke: ct.grid }}
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fill: ct.axis, fontSize: 11 }}
              axisLine={{ stroke: ct.grid }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: ct.tooltipBg,
                border: `1px solid ${ct.tooltipBorder}`,
                borderRadius: '8px',
                fontSize: '12px',
              }}
              formatter={(value: number) => [`${value.toFixed(1)}`, 'Score medio']}
              labelFormatter={(label, payload) => {
                if (payload?.[0]) return payload[0].payload.fullName
                return label
              }}
            />
            <Bar dataKey="score" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={index} fill={getRiskColor(entry.score)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
