import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  formatDateTime,
  nowDateTimeInput,
  nowIso,
  toDateTimeInput,
  toIso,
} from './format'

describe('toIso', () => {
  it('serializes a datetime-local value as local wall-clock time with seconds', () => {
    expect(toIso('2026-11-22T00:07')).toBe('2026-11-22T00:07:00')
  })

  it('keeps seconds that are already present', () => {
    expect(toIso('2026-11-22T00:07:30')).toBe('2026-11-22T00:07:30')
  })

  it('does not convert the local time to UTC', () => {
    // A UTC conversion shifts by the browser offset and appends "Z".
    expect(toIso('2026-11-22T00:07')).not.toContain('Z')
    expect(toIso('2026-11-22T00:07')).toBe('2026-11-22T00:07:00')
  })

  it('returns undefined for empty input', () => {
    expect(toIso('')).toBeUndefined()
  })

  it('returns undefined for a value that is not a datetime-local string', () => {
    expect(toIso('2026-11-22')).toBeUndefined()
  })
})

describe('reading a stored value back', () => {
  it('shows a stored naive datetime as the entered wall-clock time', () => {
    const stored = toIso('2026-11-22T00:07') as string
    expect(toDateTimeInput(stored)).toBe('2026-11-22T00:07')
    expect(formatDateTime(stored)).toBe('2026-11-22 00:07')
  })
})

describe('nowIso', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 10, 22, 0, 7, 0))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('uses the current local wall-clock time with seconds', () => {
    expect(nowDateTimeInput()).toBe('2026-11-22T00:07')
    expect(nowIso()).toBe('2026-11-22T00:07:00')
    expect(nowIso()).not.toContain('Z')
  })
})
