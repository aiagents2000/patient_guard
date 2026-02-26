'use client'

import { cn } from '@/lib/utils'
import { createContext, useContext, useState } from 'react'

const TabsContext = createContext<{
  value: string
  onChange: (v: string) => void
}>({ value: '', onChange: () => {} })

export function Tabs({
  defaultValue,
  children,
  className,
}: {
  defaultValue: string
  children: React.ReactNode
  className?: string
}) {
  const [value, setValue] = useState(defaultValue)
  return (
    <TabsContext.Provider value={{ value, onChange: setValue }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  )
}

export function TabsList({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn('flex gap-1 border-b border-border pb-0', className)}>
      {children}
    </div>
  )
}

export function TabsTrigger({
  value,
  children,
  className,
}: {
  value: string
  children: React.ReactNode
  className?: string
}) {
  const ctx = useContext(TabsContext)
  const active = ctx.value === value
  return (
    <button
      onClick={() => ctx.onChange(value)}
      className={cn(
        'px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-[1px]',
        active
          ? 'border-accent text-text-primary'
          : 'border-transparent text-text-muted hover:text-text-secondary',
        className
      )}
    >
      {children}
    </button>
  )
}

export function TabsContent({
  value,
  children,
  className,
}: {
  value: string
  children: React.ReactNode
  className?: string
}) {
  const ctx = useContext(TabsContext)
  if (ctx.value !== value) return null
  return <div className={cn('pt-4', className)}>{children}</div>
}
