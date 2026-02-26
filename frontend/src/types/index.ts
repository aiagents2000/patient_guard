// Tipi TypeScript per PatientGuard

export interface Patient {
  id: string
  name: string
  age: number
  gender: 'M' | 'F'
  fiscal_code?: string
  department: string
  admission_date: string
  is_active: boolean
}

export interface PatientSummaryItem {
  id: string
  name: string
  age: number
  gender: string
  department: string
  admission_date: string | null
  is_active: boolean
  risk_score: number
  risk_level: RiskLevel
  readmission_probability: number
  readmission_label: string
}

export type RiskLevel = 'basso' | 'medio' | 'alto' | 'critico'

export interface RiskFactor {
  factor: string
  impact: 'alto' | 'medio' | 'basso'
  contribution: number
}

export interface Prediction {
  risk_score: number
  risk_level: RiskLevel
  readmission_probability: number
  readmission_label: string
  predicted_los_days: number
  risk_factors: RiskFactor[]
  base_risk_score?: number
  model_version: string
}

export interface Vitals {
  timestamp?: string
  systolic_bp: number
  diastolic_bp: number
  heart_rate: number
  spo2: number
  temperature: number
  glucose: number
  creatinine: number
  hemoglobin: number
}

export interface Condition {
  icd10_code: string
  description: string
  is_active: boolean
  onset_date?: string
}

export interface Medication {
  name: string
  dosage: string
  frequency: string
  is_active?: boolean
}

export interface ClinicalNote {
  author: string
  note_type: 'admission' | 'progress' | 'discharge' | 'consultation'
  content: string
  timestamp: string | null
}

export interface EncounterHistory {
  date: string | null
  department: string
  los_days: number
  type: string
}

export interface PatientDetail extends Patient {
  conditions: Condition[]
  medications: Medication[]
  vitals: Vitals
  prediction: Prediction
  risk_trend: { date: string; score: number }[]
  encounters_history: EncounterHistory[]
  clinical_notes: ClinicalNote[]
}

export interface PatientRecord {
  conditions: Condition[]
  medications: Medication[]
  vitals: Vitals
  clinical_notes: ClinicalNote[]
  encounters_history: EncounterHistory[]
}

export interface Alert {
  id: string
  patient_id: string
  patient_name: string
  alert_type: 'critical_vitals' | 'risk_increase' | 'readmission_warning' | 'lab_critical'
  severity: 'low' | 'medium' | 'high' | 'critical'
  message: string
  is_read: boolean
  is_resolved: boolean
  created_at: string | null
}

export interface RiskDistribution {
  basso: number
  medio: number
  alto: number
  critico: number
}

export interface StatsOverview {
  total_patients: number
  active_patients: number
  avg_risk_score: number
  risk_distribution: RiskDistribution
  active_alerts: number
}

export interface DepartmentStats {
  department: string
  patient_count: number
  avg_risk_score: number
  critical_count: number
  high_count: number
}

export interface LLMSummary {
  patient_id: string
  summary: string
  generated_at: string
  model: string
}

export interface PredictionHistoryItem {
  date?: string
  risk_score: number
  model_version?: string
  created_at?: string
}
