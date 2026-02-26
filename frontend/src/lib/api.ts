// Client API per comunicare con il backend FastAPI

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

// --- Pazienti ---

import type {
  Alert,
  DepartmentStats,
  LLMSummary,
  PatientDetail,
  PatientRecord,
  PatientSummaryItem,
  Prediction,
  PredictionHistoryItem,
  StatsOverview,
  Vitals,
} from '@/types'

export async function fetchPatients(filters?: {
  search?: string
  risk_level?: string
  department?: string
  limit?: number
}): Promise<PatientSummaryItem[]> {
  const params = new URLSearchParams()
  if (filters?.search) params.set('search', filters.search)
  if (filters?.risk_level) params.set('risk_level', filters.risk_level)
  if (filters?.department) params.set('department', filters.department)
  if (filters?.limit) params.set('limit', String(filters.limit))
  const qs = params.toString()
  return fetchAPI(`/api/v1/patients${qs ? '?' + qs : ''}`)
}

export async function fetchPatientDetail(id: string): Promise<PatientDetail> {
  return fetchAPI(`/api/v1/patients/${id}`)
}

export async function fetchPatientVitals(id: string): Promise<Vitals[]> {
  return fetchAPI(`/api/v1/patients/${id}/vitals`)
}

export async function fetchPatientPredictions(id: string): Promise<PredictionHistoryItem[]> {
  return fetchAPI(`/api/v1/patients/${id}/predictions`)
}

export async function fetchPatientRecord(id: string): Promise<PatientRecord> {
  return fetchAPI(`/api/v1/patients/${id}/record`)
}

export async function triggerPrediction(id: string): Promise<Prediction> {
  return fetchAPI(`/api/v1/patients/${id}/predict`, { method: 'POST' })
}

export async function fetchPatientSummary(id: string): Promise<LLMSummary> {
  return fetchAPI(`/api/v1/patients/${id}/summary`)
}

// --- Alert ---

export async function fetchAlerts(filters?: {
  severity?: string
  is_read?: boolean
  limit?: number
}): Promise<Alert[]> {
  const params = new URLSearchParams()
  if (filters?.severity) params.set('severity', filters.severity)
  if (filters?.is_read !== undefined) params.set('is_read', String(filters.is_read))
  if (filters?.limit) params.set('limit', String(filters.limit))
  const qs = params.toString()
  return fetchAPI(`/api/v1/alerts${qs ? '?' + qs : ''}`)
}

export async function markAlertRead(alertId: string): Promise<Alert> {
  return fetchAPI(`/api/v1/alerts/${alertId}/read`, { method: 'PATCH' })
}

export async function resolveAlert(alertId: string): Promise<Alert> {
  return fetchAPI(`/api/v1/alerts/${alertId}/resolve`, { method: 'PATCH' })
}

// --- Statistiche ---

export async function fetchStatsOverview(): Promise<StatsOverview> {
  return fetchAPI('/api/v1/stats/overview')
}

export async function fetchStatsDepartment(): Promise<DepartmentStats[]> {
  return fetchAPI('/api/v1/stats/department')
}
