import { Shield } from 'lucide-react'

export const metadata = {
  title: 'PatientGuard — Il Mio Portale Salute',
}

export default function PatientPortalLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-white text-gray-900">
      {/* Header accessibile */}
      <header className="sticky top-0 z-30 border-b border-gray-200 bg-white/95 backdrop-blur-sm">
        <div className="mx-auto flex h-16 max-w-3xl items-center justify-between px-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600">
              <Shield className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900">PatientGuard</h1>
              <p className="text-xs text-gray-500">Il Mio Portale Salute</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm font-medium text-gray-700">Benvenuto</p>
            <p className="text-xs text-gray-500">
              {new Date().toLocaleDateString('it-IT', {
                day: 'numeric',
                month: 'long',
                year: 'numeric',
              })}
            </p>
          </div>
        </div>
      </header>

      {/* Contenuto principale */}
      <main className="mx-auto max-w-3xl px-4 py-6">{children}</main>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-gray-50 py-6 text-center">
        <p className="text-sm text-gray-500">
          Le informazioni mostrate sono a scopo informativo.
          <br />
          Per qualsiasi dubbio, contatta il tuo medico curante.
        </p>
      </footer>
    </div>
  )
}
