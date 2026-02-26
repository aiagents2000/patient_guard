'use client'

import { Bell, MapPin, Moon, Sun } from 'lucide-react'
import { useEffect, useState } from 'react'
import { fetchAlerts } from '@/lib/api'
import { useTheme } from '@/components/ThemeProvider'
import type { Alert } from '@/types'

export default function TopBar() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [showDropdown, setShowDropdown] = useState(false)
  const { theme, toggleTheme } = useTheme()
  const unreadCount = alerts.filter((a) => !a.is_read).length

  useEffect(() => {
    fetchAlerts({ limit: 10 })
      .then(setAlerts)
      .catch(() => {})
  }, [])

  const now = new Date().toLocaleDateString('it-IT', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-border bg-card/80 backdrop-blur-sm px-4 sm:px-6">
      <div className="flex items-center gap-2 text-sm text-text-muted pl-10 lg:pl-0">
        <MapPin className="h-3.5 w-3.5 hidden sm:block" />
        <span className="hidden sm:inline">Milano — @MIND Hub</span>
        <span className="hidden sm:inline mx-2 text-border">|</span>
        <span className="capitalize">{now}</span>
      </div>

      <div className="flex items-center gap-1">
        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="flex h-9 w-9 items-center justify-center rounded-lg hover:bg-elevated transition-colors"
          title={theme === 'dark' ? 'Tema chiaro' : 'Tema scuro'}
        >
          {theme === 'dark' ? (
            <Sun className="h-4 w-4 text-text-secondary" />
          ) : (
            <Moon className="h-4 w-4 text-text-secondary" />
          )}
        </button>

        {/* Alerts */}
        <div className="relative">
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            className="relative flex h-9 w-9 items-center justify-center rounded-lg hover:bg-elevated transition-colors"
          >
            <Bell className="h-4.5 w-4.5 text-text-secondary" />
            {unreadCount > 0 && (
              <span className="absolute -right-0.5 -top-0.5 flex h-4.5 min-w-[18px] items-center justify-center rounded-full bg-risk-critico px-1 text-[10px] font-bold text-white">
                {unreadCount}
              </span>
            )}
          </button>

          {/* Alert dropdown */}
          {showDropdown && (
            <div className="absolute right-0 top-11 w-96 rounded-xl border border-border bg-card shadow-2xl">
              <div className="border-b border-border px-4 py-3">
                <h3 className="text-sm font-semibold text-text-primary">
                  Alert ({unreadCount} non letti)
                </h3>
              </div>
              <div className="max-h-80 overflow-y-auto">
                {alerts.slice(0, 8).map((alert) => (
                  <div
                    key={alert.id}
                    className={`flex gap-3 border-b border-border/50 px-4 py-3 ${
                      !alert.is_read ? 'bg-elevated/50' : ''
                    }`}
                  >
                    <div
                      className="mt-1 h-2 w-2 flex-shrink-0 rounded-full"
                      style={{
                        backgroundColor:
                          alert.severity === 'critical'
                            ? '#ef4444'
                            : alert.severity === 'high'
                            ? '#f97316'
                            : '#f59e0b',
                      }}
                    />
                    <div className="min-w-0">
                      <p className="text-xs font-medium text-text-primary truncate">
                        {alert.patient_name}
                      </p>
                      <p className="text-[11px] text-text-muted line-clamp-2 mt-0.5">
                        {alert.message}
                      </p>
                    </div>
                  </div>
                ))}
                {alerts.length === 0 && (
                  <p className="px-4 py-6 text-center text-sm text-text-muted">
                    Nessun alert
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
