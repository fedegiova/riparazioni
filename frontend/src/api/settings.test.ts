import { describe, expect, it } from 'vitest'
import {
  parseHolidays,
  parseOperators,
  parseWorkingHours,
  serializeHolidays,
  serializeOperators,
  serializeWorkingHours,
} from './settings'

describe('parseOperators', () => {
  it('keeps strings and drops other items', () => {
    expect(parseOperators(['A', 3, 'B'])).toEqual(['A', 'B'])
  })

  it('returns an empty array for a non-array value', () => {
    expect(parseOperators(null)).toEqual([])
    expect(parseOperators({ a: 1 })).toEqual([])
  })
})

describe('parseWorkingHours', () => {
  it('keeps valid intervals per weekday and drops empty days', () => {
    expect(
      parseWorkingHours({ mon: [['08:00', '12:00']], sun: [] }),
    ).toEqual({ mon: [['08:00', '12:00']] })
  })

  it('drops malformed intervals and unknown weekdays', () => {
    expect(
      parseWorkingHours({ mon: [['08:00']], funday: [['08:00', '12:00']] }),
    ).toEqual({})
  })

  it('returns an empty object for a non-object value', () => {
    expect(parseWorkingHours('nope')).toEqual({})
  })
})

describe('parseHolidays', () => {
  it('keeps ranges with string fields', () => {
    const range = { from: '2026-01-01', to: '2026-01-01', name: 'Capodanno' }
    expect(parseHolidays({ '2026': [range] })).toEqual({ '2026': [range] })
  })

  it('drops malformed ranges and non-array years', () => {
    expect(parseHolidays({ '2026': [{ from: 1 }], '2027': 'nope' })).toEqual({
      '2026': [],
    })
  })

  it('returns an empty object for a non-object value', () => {
    expect(parseHolidays(42)).toEqual({})
  })
})

describe('serializeOperators', () => {
  it('trims names and drops blanks', () => {
    expect(serializeOperators([' A ', '', 'B'])).toEqual(['A', 'B'])
  })
})

describe('serializeWorkingHours', () => {
  it('fills every weekday with an empty list for closed days', () => {
    expect(serializeWorkingHours({ mon: [['08:00', '12:00']] })).toEqual({
      mon: [['08:00', '12:00']],
      tue: [],
      wed: [],
      thu: [],
      fri: [],
      sat: [],
      sun: [],
    })
  })
})

describe('serializeHolidays', () => {
  it('drops years with no ranges', () => {
    const range = { from: '2027-01-01', to: '2027-01-01', name: 'Y' }
    expect(serializeHolidays({ '2026': [], '2027': [range] })).toEqual({
      '2027': [range],
    })
  })
})
