'use client'

import { useEffect, useState } from 'react'
import { Check, ExternalLink, Moon, Server, Sun } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useTheme } from '@/components/ThemeProvider'

interface BackendHealth {
  status: string
  version: string
  mode: string
  llm_available: boolean
}

export default function SettingsPage() {
  const { theme, toggleTheme } = useTheme()
  const [health, setHealth] = useState<BackendHealth | null>(null)
  const [healthError, setHealthError] = useState(false)
  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

  useEffect(() => {
    fetch(`${apiBase}/health`)
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setHealthError(true))
  }, [apiBase])

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-text-primary mb-1">Impostazioni</h2>
        <p className="text-sm text-text-muted">
          Configurazione e stato del sistema
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Theme */}
        <Card>
          <CardHeader>
            <CardTitle>Tema interfaccia</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-3">
              <button
                onClick={() => theme !== 'dark' && toggleTheme()}
                className={`flex-1 flex flex-col items-center gap-2 rounded-xl border-2 p-4 transition-colors ${
                  theme === 'dark'
                    ? 'border-accent bg-accent/10'
                    : 'border-border hover:border-text-muted'
                }`}
              >
                <Moon className="h-6 w-6 text-text-secondary" />
                <span className="text-sm font-medium text-text-primary">Scuro</span>
                {theme === 'dark' && <Check className="h-4 w-4 text-accent" />}
              </button>
              <button
                onClick={() => theme !== 'light' && toggleTheme()}
                className={`flex-1 flex flex-col items-center gap-2 rounded-xl border-2 p-4 transition-colors ${
                  theme === 'light'
                    ? 'border-accent bg-accent/10'
                    : 'border-border hover:border-text-muted'
                }`}
              >
                <Sun className="h-6 w-6 text-text-secondary" />
                <span className="text-sm font-medium text-text-primary">Chiaro</span>
                {theme === 'light' && <Check className="h-4 w-4 text-accent" />}
              </button>
            </div>
          </CardContent>
        </Card>

        {/* Backend Status */}
        <Card>
          <CardHeader>
            <CardTitle>Stato Backend</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {healthError ? (
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-risk-critico" />
                <span className="text-sm text-risk-critico font-medium">Offline</span>
              </div>
            ) : health ? (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-risk-basso" />
                  <span className="text-sm text-risk-basso font-medium">Online</span>
                  <span className="text-xs text-text-muted">v{health.version}</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="rounded-lg bg-elevated p-2">
                    <p className="text-text-muted">Modalità dati</p>
                    <p className="font-medium text-text-primary mt-0.5">
                      {health.mode === 'supabase' ? 'Supabase' : 'JSON Demo'}
                    </p>
                  </div>
                  <div className="rounded-lg bg-elevated p-2">
                    <p className="text-text-muted">LLM</p>
                    <p className="font-medium text-text-primary mt-0.5">
                      {health.llm_available ? 'Attivo' : 'Rule-based'}
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-16 bg-elevated rounded animate-pulse" />
            )}
            <a
              href={`${apiBase}/docs`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-accent hover:underline"
            >
              <Server className="h-3 w-3" />
              API Docs
              <ExternalLink className="h-3 w-3" />
            </a>
          </CardContent>
        </Card>

        {/* About */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>PatientGuard</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-text-secondary leading-relaxed">
              Piattaforma AI per analisi predittiva delle cartelle cliniche elettroniche nel Servizio
              Sanitario Nazionale italiano. Sviluppata per HSIL Hackathon 2026.
            </p>
            <div className="flex flex-wrap gap-2 mt-3">
              {['Next.js 14', 'FastAPI', 'XGBoost', 'TypeScript', 'Tailwind CSS', 'Recharts'].map(
                (tech) => (
                  <span
                    key={tech}
                    className="rounded-full bg-elevated px-3 py-1 text-xs text-text-muted"
                  >
                    {tech}
                  </span>
                )
              )}
            </div>
            <div className="mt-4">
              <a
                href="https://github.com/aiagents2000/patient_guard"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs text-accent hover:underline"
              >
                GitHub Repository
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
