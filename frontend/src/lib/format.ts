export function formatHours(hours: number | null | undefined): string {
  if (hours === null || hours === undefined) return '—'
  const totalMinutes = Math.round(hours * 60)
  const h = Math.floor(totalMinutes / 60)
  const m = totalMinutes % 60
  return m === 0 ? `${h}h` : `${h}h ${m}m`
}

/** Date-only values are already ISO `YYYY-MM-DD`; keep them terse. */
export function formatDate(value: string | null | undefined): string {
  return value ? value.slice(0, 10) : '—'
}

export function formatDateTime(value: string | null | undefined): string {
  return value ? value.replace('T', ' ').slice(0, 16) : '—'
}

export function toDateInput(value: string | null | undefined): string {
  return value ? value.slice(0, 10) : ''
}

export function toDateTimeInput(value: string | null | undefined): string {
  return value ? value.slice(0, 16) : ''
}

/** Current local date/time shaped for an `<input type="datetime-local">`. */
export function nowDateTimeInput(): string {
  const now = new Date()
  const pad = (value: number) => String(value).padStart(2, '0')
  return (
    `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}` +
    `T${pad(now.getHours())}:${pad(now.getMinutes())}`
  )
}

export function toIso(value: string): string | undefined {
  if (!value) return undefined
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? undefined : parsed.toISOString()
}
