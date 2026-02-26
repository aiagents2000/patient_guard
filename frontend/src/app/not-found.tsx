import Link from 'next/link'
import { Shield } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/10 mb-6">
        <Shield className="h-7 w-7 text-accent" />
      </div>
      <h1 className="text-6xl font-bold font-display text-text-primary mb-2">404</h1>
      <p className="text-lg text-text-secondary mb-6">Pagina non trovata</p>
      <p className="text-sm text-text-muted mb-8 text-center max-w-md">
        La pagina che stai cercando non esiste o è stata spostata.
      </p>
      <Link
        href="/dashboard"
        className="rounded-lg bg-accent px-6 py-2.5 text-sm font-medium text-white hover:bg-accent/90 transition-colors"
      >
        Torna alla Dashboard
      </Link>
    </div>
  )
}
