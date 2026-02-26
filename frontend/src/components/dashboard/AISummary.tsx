'use client'

import { Bot, RefreshCw } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { fetchPatientSummary } from '@/lib/api'
import type { LLMSummary } from '@/types'

interface Props {
  patientId: string
}

export default function AISummary({ patientId }: Props) {
  const [summary, setSummary] = useState<LLMSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  const load = () => {
    setLoading(true)
    setError(false)
    fetchPatientSummary(patientId)
      .then(setSummary)
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [patientId])

  return (
    <Card className="border-accent/30">
      <CardHeader className="flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <Bot className="h-4 w-4 text-accent" />
          <CardTitle className="text-accent">Riassunto AI</CardTitle>
        </div>
        <Button variant="ghost" size="sm" onClick={load} disabled={loading}>
          <RefreshCw className={`h-3 w-3 mr-1 ${loading ? 'animate-spin' : ''}`} />
          Rigenera
        </Button>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2">
            <div className="h-3 bg-elevated rounded w-full animate-pulse" />
            <div className="h-3 bg-elevated rounded w-5/6 animate-pulse" />
            <div className="h-3 bg-elevated rounded w-4/6 animate-pulse" />
          </div>
        ) : error ? (
          <p className="text-sm text-text-muted">
            Impossibile generare il riassunto. Riprova.
          </p>
        ) : summary ? (
          <div>
            <div className="text-sm text-text-secondary leading-relaxed whitespace-pre-line">
              {summary.summary}
            </div>
            <p className="text-[10px] text-text-muted mt-3">
              Generato: {new Date(summary.generated_at).toLocaleString('it-IT')} — Modello:{' '}
              {summary.model}
            </p>
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}
