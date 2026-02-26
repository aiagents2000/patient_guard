'use client'

import { ArrowLeft, RefreshCw, User } from 'lucide-react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useEffect, useState } from 'react'

import AISummary from '@/components/dashboard/AISummary'
import ClinicalRecord from '@/components/dashboard/ClinicalRecord'
import RiskFactorsChart from '@/components/dashboard/RiskFactorsChart'
import RiskGauge from '@/components/dashboard/RiskGauge'
import TrendChart from '@/components/dashboard/TrendChart'
import VitalsGrid from '@/components/dashboard/VitalsGrid'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { fetchPatientDetail, triggerPrediction } from '@/lib/api'
import { getReadmissionColor, getRiskBgClass } from '@/lib/utils'
import type { PatientDetail } from '@/types'

export default function PatientDetailPage() {
  const params = useParams()
  const patientId = params.id as string
  const [patient, setPatient] = useState<PatientDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [predicting, setPredicting] = useState(false)

  useEffect(() => {
    setLoading(true)
    fetchPatientDetail(patientId)
      .then(setPatient)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [patientId])

  const handlePredict = async () => {
    setPredicting(true)
    try {
      const newPred = await triggerPrediction(patientId)
      setPatient((prev) =>
        prev ? { ...prev, prediction: { ...prev.prediction, ...newPred } } : prev
      )
    } catch {
      // errore silenzioso
    } finally {
      setPredicting(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-10 w-48 bg-elevated rounded animate-pulse" />
        <div className="h-64 bg-elevated rounded animate-pulse" />
      </div>
    )
  }

  if (!patient) {
    return (
      <div className="text-center py-20">
        <p className="text-text-muted">Paziente non trovato</p>
        <Link href="/dashboard" className="text-accent text-sm mt-2 inline-block hover:underline">
          Torna alla dashboard
        </Link>
      </div>
    )
  }

  const pred = patient.prediction
  const readmColor = getReadmissionColor(pred.readmission_probability)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Link href="/dashboard">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-1" /> Dashboard
            </Button>
          </Link>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent/20">
              <User className="h-5 w-5 text-accent" />
            </div>
            <div className="min-w-0">
              <h2 className="text-lg font-bold text-text-primary truncate">{patient.name}</h2>
              <p className="text-xs text-text-muted truncate">
                {patient.age} anni, {patient.gender} — {patient.department}
                {patient.fiscal_code && ` — CF: ${patient.fiscal_code}`}
              </p>
            </div>
          </div>
        </div>
        <Button onClick={handlePredict} disabled={predicting} size="sm" className="self-start sm:self-auto">
          <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${predicting ? 'animate-spin' : ''}`} />
          Ricalcola rischio
        </Button>
      </div>

      {/* Risk Score + Prediction cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Gauge */}
        <Card className="flex flex-col items-center justify-center py-4">
          <RiskGauge score={pred.risk_score} />
          <Badge
            variant={`risk-${pred.risk_level}` as 'risk-basso' | 'risk-medio' | 'risk-alto' | 'risk-critico'}
            className="mt-2 text-sm px-3"
          >
            Rischio {pred.risk_level.charAt(0).toUpperCase() + pred.risk_level.slice(1)}
          </Badge>
        </Card>

        {/* Readmission */}
        <Card>
          <CardHeader>
            <CardTitle>Riospedalizzazione 30gg</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center">
            <span
              className="font-display text-3xl font-bold"
              style={{ color: readmColor }}
            >
              {(pred.readmission_probability * 100).toFixed(1)}%
            </span>
            <span
              className="mt-2 rounded-full px-3 py-1 text-xs font-semibold"
              style={{
                backgroundColor: readmColor + '20',
                color: readmColor,
              }}
            >
              {pred.readmission_label}
            </span>
          </CardContent>
        </Card>

        {/* LOS */}
        <Card>
          <CardHeader>
            <CardTitle>Degenza Prevista</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center">
            <span className="font-display text-3xl font-bold text-accent">
              {pred.predicted_los_days}
            </span>
            <span className="text-xs text-text-muted mt-1">giorni</span>
            <span className="text-[10px] text-text-muted mt-2">
              Modello v{pred.model_version}
            </span>
          </CardContent>
        </Card>
      </div>

      {/* Trend + Risk Factors */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <TrendChart data={patient.risk_trend} />
        <RiskFactorsChart factors={pred.risk_factors} />
      </div>

      {/* Vitals */}
      <div>
        <h3 className="text-base font-semibold text-text-primary mb-3">Parametri Vitali</h3>
        <VitalsGrid vitals={patient.vitals} />
      </div>

      {/* AI Summary */}
      <AISummary patientId={patientId} />

      {/* Clinical Record */}
      <ClinicalRecord
        conditions={patient.conditions}
        medications={patient.medications}
        clinical_notes={patient.clinical_notes}
        encounters_history={patient.encounters_history}
      />
    </div>
  )
}
