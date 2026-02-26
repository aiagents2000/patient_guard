'use client'

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { getChartTheme, getRiskColor } from '@/lib/utils'
import { useTheme } from '@/components/ThemeProvider'

interface Props {
  data: { date: string; score: number }[]
}

export default function TrendChart({ data }: Props) {
  useTheme() // re-render on theme change
  const ct = getChartTheme()

  if (!data || data.length === 0) {
    return <Card className="h-64 animate-pulse" />
  }

  const lastScore = data[data.length - 1]?.score ?? 0
  const color = getRiskColor(lastScore)

  const chartData = data.map((d) => ({
    ...d,
    dateLabel: new Date(d.date).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
    }),
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle>Trend Risk Score (7 giorni)</CardTitle>
      </CardHeader>
      <CardContent className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: -10 }}>
            <defs>
              <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                <stop offset="95%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
            <XAxis
              dataKey="dateLabel"
              tick={{ fill: ct.axis, fontSize: 10 }}
              axisLine={{ stroke: ct.grid }}
            />
            <YAxis
              domain={[0, 100]}
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
            />
            <Area
              type="monotone"
              dataKey="score"
              stroke={color}
              strokeWidth={2}
              fill="url(#riskGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
