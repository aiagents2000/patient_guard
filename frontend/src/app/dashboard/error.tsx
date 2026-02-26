'use client'

import { AlertTriangle, RefreshCw } from 'lucide-react'

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-4">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-risk-critico/10 mb-6">
        <AlertTriangle className="h-7 w-7 text-risk-critico" />
      </div>
      <h2 className="text-xl font-bold text-text-primary mb-2">Qualcosa è andato storto</h2>
      <p className="text-sm text-text-muted mb-6 text-center max-w-md">
        Si è verificato un errore nel caricamento della pagina. Riprova o torna alla dashboard.
      </p>
      <button
        onClick={reset}
        className="flex items-center gap-2 rounded-lg bg-accent px-5 py-2.5 text-sm font-medium text-white hover:bg-accent/90 transition-colors"
      >
        <RefreshCw className="h-4 w-4" />
        Riprova
      </button>
    </div>
  )
}
