'use client'

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { formatDate, formatDateTime } from '@/lib/utils'
import type { ClinicalNote, Condition, EncounterHistory, Medication } from '@/types'

interface Props {
  conditions: Condition[]
  medications: Medication[]
  clinical_notes: ClinicalNote[]
  encounters_history: EncounterHistory[]
}

export default function ClinicalRecord({
  conditions,
  medications,
  clinical_notes,
  encounters_history,
}: Props) {
  return (
    <Card className="mt-6">
      <div className="p-4">
        <h3 className="text-base font-semibold text-text-primary mb-4">Cartella Clinica</h3>
        <Tabs defaultValue="diagnosi">
          <TabsList>
            <TabsTrigger value="diagnosi">Diagnosi ({conditions.length})</TabsTrigger>
            <TabsTrigger value="terapia">Terapia ({medications.length})</TabsTrigger>
            <TabsTrigger value="note">Note ({clinical_notes.length})</TabsTrigger>
            <TabsTrigger value="storico">Ricoveri ({encounters_history.length})</TabsTrigger>
          </TabsList>

          {/* Diagnosi */}
          <TabsContent value="diagnosi">
            {conditions.length === 0 ? (
              <p className="text-sm text-text-muted">Nessuna diagnosi registrata</p>
            ) : (
              <div className="space-y-2">
                {conditions.map((c, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between rounded-lg bg-elevated/50 px-3 py-2"
                  >
                    <div>
                      <span className="text-xs text-text-muted font-mono mr-2">
                        {c.icd10_code}
                      </span>
                      <span className="text-sm text-text-primary">{c.description}</span>
                    </div>
                    <Badge variant={c.is_active ? 'risk-alto' : 'default'}>
                      {c.is_active ? 'Attiva' : 'Risolta'}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Terapia */}
          <TabsContent value="terapia">
            {medications.length === 0 ? (
              <p className="text-sm text-text-muted">Nessun farmaco in terapia</p>
            ) : (
              <table className="w-full">
                <thead>
                  <tr className="text-xs text-text-muted uppercase border-b border-border">
                    <th className="py-2 text-left">Farmaco</th>
                    <th className="py-2 text-left">Dosaggio</th>
                    <th className="py-2 text-left">Frequenza</th>
                  </tr>
                </thead>
                <tbody>
                  {medications.map((m, i) => (
                    <tr key={i} className="border-b border-border/50">
                      <td className="py-2 text-sm text-text-primary font-medium">{m.name}</td>
                      <td className="py-2 text-sm text-text-secondary">{m.dosage || '—'}</td>
                      <td className="py-2 text-sm text-text-secondary">{m.frequency || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </TabsContent>

          {/* Note cliniche */}
          <TabsContent value="note">
            {clinical_notes.length === 0 ? (
              <p className="text-sm text-text-muted">Nessuna nota clinica</p>
            ) : (
              <div className="space-y-3">
                {clinical_notes.map((n, i) => (
                  <div key={i} className="rounded-lg bg-elevated/50 p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="default">
                        {n.note_type === 'admission'
                          ? 'Ammissione'
                          : n.note_type === 'progress'
                          ? 'Decorso'
                          : n.note_type === 'discharge'
                          ? 'Dimissione'
                          : 'Consulenza'}
                      </Badge>
                      <span className="text-xs text-text-muted">{n.author}</span>
                      <span className="text-xs text-text-muted ml-auto">
                        {formatDateTime(n.timestamp)}
                      </span>
                    </div>
                    <p className="text-sm text-text-secondary leading-relaxed">{n.content}</p>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Storico ricoveri */}
          <TabsContent value="storico">
            {encounters_history.length === 0 ? (
              <p className="text-sm text-text-muted">Nessun ricovero precedente</p>
            ) : (
              <table className="w-full">
                <thead>
                  <tr className="text-xs text-text-muted uppercase border-b border-border">
                    <th className="py-2 text-left">Data</th>
                    <th className="py-2 text-left">Reparto</th>
                    <th className="py-2 text-left">Degenza</th>
                    <th className="py-2 text-left">Tipo</th>
                  </tr>
                </thead>
                <tbody>
                  {encounters_history.map((e, i) => (
                    <tr key={i} className="border-b border-border/50">
                      <td className="py-2 text-sm text-text-primary">{formatDate(e.date)}</td>
                      <td className="py-2 text-sm text-text-secondary">{e.department}</td>
                      <td className="py-2 text-sm text-text-secondary">{e.los_days} gg</td>
                      <td className="py-2 text-sm text-text-secondary capitalize">{e.type}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </Card>
  )
}
