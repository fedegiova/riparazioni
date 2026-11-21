// Data access and shape helpers for application settings. The API exchanges
// JSON values (typed as `unknown` in the generated client), so this module
// owns the local types for the known settings and the parse/serialize
// boundary between the API and the settings page.
import { api } from './client'

export const WEEKDAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'] as const
export type Weekday = (typeof WEEKDAYS)[number]

/** One working interval as `[begin, end]` HH:MM times. */
export type WorkingInterval = [string, string]
/** Weekday -> that day's working intervals (missing/empty day means closed). */
export type WorkingHours = Partial<Record<Weekday, WorkingInterval[]>>

/** A named holiday range with ISO dates inside its year. */
export type HolidayRange = { from: string; to: string; name: string }
/** Four-digit year -> that year's holiday ranges. */
export type Holidays = Record<string, HolidayRange[]>

export type Operators = string[]
export type GasTypes = string[]

// --- parse (API -> typed state) ---------------------------------------------

export function parseOperators(value: unknown): Operators {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === 'string')
    : []
}

export function parseGasTypes(value: unknown): GasTypes {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === 'string')
    : []
}

export function parseWorkingHours(value: unknown): WorkingHours {
  const result: WorkingHours = {}
  if (typeof value !== 'object' || value === null) return result
  const source = value as Record<string, unknown>
  for (const day of WEEKDAYS) {
    const intervals = source[day]
    if (!Array.isArray(intervals)) continue
    const parsed: WorkingInterval[] = []
    for (const interval of intervals) {
      if (
        Array.isArray(interval) &&
        interval.length === 2 &&
        typeof interval[0] === 'string' &&
        typeof interval[1] === 'string'
      ) {
        parsed.push([interval[0], interval[1]])
      }
    }
    if (parsed.length > 0) result[day] = parsed
  }
  return result
}

export function parseHolidays(value: unknown): Holidays {
  const result: Holidays = {}
  if (typeof value !== 'object' || value === null) return result
  for (const [year, ranges] of Object.entries(value as Record<string, unknown>)) {
    if (!Array.isArray(ranges)) continue
    const parsed: HolidayRange[] = []
    for (const range of ranges) {
      const candidate = range as Partial<HolidayRange>
      if (
        typeof candidate === 'object' &&
        candidate !== null &&
        typeof candidate.from === 'string' &&
        typeof candidate.to === 'string' &&
        typeof candidate.name === 'string'
      ) {
        parsed.push({ from: candidate.from, to: candidate.to, name: candidate.name })
      }
    }
    result[year] = parsed
  }
  return result
}

// --- serialize (typed state -> API) -----------------------------------------

/** Trim names and drop blanks. */
export function serializeOperators(operators: Operators): Operators {
  return operators.map((name) => name.trim()).filter((name) => name !== '')
}

/** Trim names and drop blanks. */
export function serializeGasTypes(gasTypes: GasTypes): GasTypes {
  return gasTypes.map((name) => name.trim()).filter((name) => name !== '')
}

/** Always emit every weekday (an empty list means closed). */
export function serializeWorkingHours(
  hours: WorkingHours,
): Record<Weekday, WorkingInterval[]> {
  const result = {} as Record<Weekday, WorkingInterval[]>
  for (const day of WEEKDAYS) {
    result[day] = (hours[day] ?? []).map(
      (interval) => [interval[0], interval[1]] as WorkingInterval,
    )
  }
  return result
}

/** Drop years with no ranges so the stored object stays sparse. */
export function serializeHolidays(holidays: Holidays): Holidays {
  const result: Holidays = {}
  for (const [year, ranges] of Object.entries(holidays)) {
    if (ranges.length > 0) {
      result[year] = ranges.map((range) => ({ ...range }))
    }
  }
  return result
}

// --- API calls ---------------------------------------------------------------

export async function listSettings(): Promise<Record<string, unknown>> {
  const { data } = await api.GET('/api/v1/settings')
  return data ?? {}
}

export async function getSetting(name: string): Promise<unknown> {
  const { data } = await api.GET('/api/v1/settings/{name}', {
    params: { path: { name } },
  })
  return data
}

/** The gas types configured in settings, used to populate the cylinder picker. */
export async function getGasTypes(): Promise<GasTypes> {
  return parseGasTypes(await getSetting('gas_types'))
}

/** The operators configured in settings, used by the work-log operator picker. */
export async function getOperators(): Promise<Operators> {
  return parseOperators(await getSetting('operators'))
}

export async function putSetting(name: string, value: unknown): Promise<unknown> {
  const { data } = await api.PUT('/api/v1/settings/{name}', {
    params: { path: { name } },
    body: value,
  })
  return data
}

export async function putSettings(
  values: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  const { data } = await api.PUT('/api/v1/settings', { body: values })
  return data ?? {}
}

export async function deleteSetting(name: string): Promise<void> {
  await api.DELETE('/api/v1/settings/{name}', { params: { path: { name } } })
}
