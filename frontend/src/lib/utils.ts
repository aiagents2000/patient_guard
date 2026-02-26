// Utility per PatientGuard frontend

import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

// Chart theme colors — resolved from CSS vars at render time
export function getChartTheme() {
  if (typeof window === 'undefined') return { grid: '#1e293b', axis: '#94a3b8', tooltipBg: '#0b1121', tooltipBorder: '#1e293b', gaugeBg: '#1e293b' }
  const style = getComputedStyle(document.documentElement)
  return {
    grid: style.getPropertyValue('--color-border').trim() || '#1e293b',
    axis: style.getPropertyValue('--color-text-secondary').trim() || '#94a3b8',
    tooltipBg: style.getPropertyValue('--color-card').trim() || '#0b1121',
    tooltipBorder: style.getPropertyValue('--color-border').trim() || '#1e293b',
    gaugeBg: style.getPropertyValue('--color-border').trim() || '#1e293b',
  }
}

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Colore risk score
export function getRiskColor(score: number): string {
  if (score <= 25) return '#10b981' // verde
  if (score <= 50) return '#f59e0b' // ambra
  if (score <= 75) return '#f97316' // arancione
  return '#ef4444' // rosso
}

export function getRiskBgClass(level: string): string {
  switch (level) {
    case 'basso': return 'bg-risk-basso/20 text-risk-basso'
    case 'medio': return 'bg-risk-medio/20 text-risk-medio'
    case 'alto': return 'bg-risk-alto/20 text-risk-alto'
    case 'critico': return 'bg-risk-critico/20 text-risk-critico'
    default: return 'bg-text-muted/20 text-text-muted'
  }
}

export function getRiskLabel(score: number): string {
  if (score <= 25) return 'Basso'
  if (score <= 50) return 'Medio'
  if (score <= 75) return 'Alto'
  return 'Critico'
}

export function getReadmissionLabel(prob: number): string {
  if (prob < 0.3) return 'NELLA NORMA'
  if (prob <= 0.7) return 'MONITORARE'
  return 'INTERVENTO URGENTE'
}

export function getReadmissionColor(prob: number): string {
  if (prob < 0.3) return '#10b981'
  if (prob <= 0.7) return '#f59e0b'
  return '#ef4444'
}

export function getSeverityColor(severity: string): string {
  switch (severity) {
    case 'critical': return '#ef4444'
    case 'high': return '#f97316'
    case 'medium': return '#f59e0b'
    case 'low': return '#10b981'
    default: return '#64748b'
  }
}

// Calcola trend dall'array di score
export function calculateTrend(scores: number[]): 'up' | 'down' | 'stable' {
  if (scores.length < 2) return 'stable'
  const recent = scores.slice(-3)
  const avg = recent.reduce((a, b) => a + b, 0) / recent.length
  const prev = scores.slice(-6, -3)
  if (prev.length === 0) return 'stable'
  const prevAvg = prev.reduce((a, b) => a + b, 0) / prev.length
  const diff = avg - prevAvg
  if (diff > 3) return 'up'
  if (diff < -3) return 'down'
  return 'stable'
}

// Formatta data
export function formatDate(date: string | null | undefined): string {
  if (!date) return '—'
  try {
    return new Date(date).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    })
  } catch {
    return date
  }
}

export function formatDateTime(date: string | null | undefined): string {
  if (!date) return '—'
  try {
    return new Date(date).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return date
  }
}

// Controlla se un valore vitale è anormale
export function isVitalAbnormal(key: string, value: number): boolean {
  const ranges: Record<string, [number, number]> = {
    systolic_bp: [90, 140],
    diastolic_bp: [60, 90],
    heart_rate: [60, 100],
    spo2: [95, 100],
    temperature: [36.0, 37.5],
    glucose: [70, 140],
    creatinine: [0.6, 1.2],
    hemoglobin: [12.0, 17.0],
  }
  const range = ranges[key]
  if (!range) return false
  return value < range[0] || value > range[1]
}

export function getVitalUnit(key: string): string {
  const units: Record<string, string> = {
    systolic_bp: 'mmHg',
    diastolic_bp: 'mmHg',
    heart_rate: 'bpm',
    spo2: '%',
    temperature: '°C',
    glucose: 'mg/dL',
    creatinine: 'mg/dL',
    hemoglobin: 'g/dL',
  }
  return units[key] || ''
}

export function getVitalLabel(key: string): string {
  const labels: Record<string, string> = {
    systolic_bp: 'PA Sistolica',
    diastolic_bp: 'PA Diastolica',
    heart_rate: 'Freq. Cardiaca',
    spo2: 'SpO2',
    temperature: 'Temperatura',
    glucose: 'Glicemia',
    creatinine: 'Creatinina',
    hemoglobin: 'Emoglobina',
  }
  return labels[key] || key
}
