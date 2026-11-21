import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import SettingsPage from './SettingsPage'

const { listSettings, putSettings } = vi.hoisted(() => ({
  listSettings: vi.fn(),
  putSettings: vi.fn(),
}))

vi.mock('../api/settings', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../api/settings')>()
  return { ...actual, listSettings, putSettings }
})

const YEAR = String(new Date().getFullYear())

function payload(overrides: Record<string, unknown> = {}) {
  return {
    operators: [],
    gas_types: [],
    working_hours: {
      mon: [],
      tue: [],
      wed: [],
      thu: [],
      fri: [],
      sat: [],
      sun: [],
    },
    holidays: {},
    ...overrides,
  }
}

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('SettingsPage', () => {
  it('loads and shows the stored settings', async () => {
    listSettings.mockResolvedValue(
      payload({
        operators: ['MARIO'],
        gas_types: ['R410A'],
        working_hours: { mon: [['08:00', '12:00']] },
        holidays: {
          [YEAR]: [{ from: `${YEAR}-01-01`, to: `${YEAR}-01-01`, name: 'Capodanno' }],
        },
      }),
    )
    render(<SettingsPage />)

    expect(await screen.findByText('MARIO')).toBeTruthy()
    expect(screen.getByText('R410A')).toBeTruthy()
    expect(screen.getByDisplayValue('08:00')).toBeTruthy()
    expect(screen.getByDisplayValue('Capodanno')).toBeTruthy()
  })

  it('adds an operator and saves it', async () => {
    listSettings.mockResolvedValue(payload())
    putSettings.mockResolvedValue(payload())
    render(<SettingsPage />)
    await screen.findByText('No operators.')

    fireEvent.change(screen.getByLabelText('Add operator'), {
      target: { value: 'LUIGI' },
    })
    fireEvent.click(screen.getAllByRole('button', { name: 'Add' })[0])
    expect(screen.getByText('LUIGI')).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(putSettings).toHaveBeenCalledTimes(1))
    expect(putSettings.mock.calls[0][0].operators).toEqual(['LUIGI'])
  })

  it('adds a gas type and saves it', async () => {
    listSettings.mockResolvedValue(payload())
    putSettings.mockResolvedValue(payload())
    render(<SettingsPage />)
    await screen.findByText('No gas types.')

    fireEvent.change(screen.getByLabelText('Add gas type'), {
      target: { value: 'R32' },
    })
    fireEvent.click(screen.getAllByRole('button', { name: 'Add' })[1])
    expect(screen.getByText('R32')).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(putSettings).toHaveBeenCalledTimes(1))
    expect(putSettings.mock.calls[0][0].gas_types).toEqual(['R32'])
  })

  it('removes a gas type and saves it', async () => {
    listSettings.mockResolvedValue(payload({ gas_types: ['R410A'] }))
    putSettings.mockResolvedValue(payload())
    render(<SettingsPage />)
    await screen.findByText('R410A')

    fireEvent.click(screen.getByTestId('CancelIcon'))
    expect(screen.queryByText('R410A')).toBeNull()

    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(putSettings).toHaveBeenCalledTimes(1))
    expect(putSettings.mock.calls[0][0].gas_types).toEqual([])
  })

  it('edits working hours and saves them', async () => {
    listSettings.mockResolvedValue(payload())
    putSettings.mockResolvedValue(payload())
    render(<SettingsPage />)
    await screen.findByText('No operators.')

    // First "Add interval" belongs to Monday.
    fireEvent.click(screen.getAllByRole('button', { name: 'Add interval' })[0])
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(putSettings).toHaveBeenCalledTimes(1))
    const body = putSettings.mock.calls[0][0]
    expect(body.working_hours.mon).toEqual([['08:00', '12:00']])
    expect(body.working_hours.sun).toEqual([])
  })

  it('adds a holiday for the selected year and saves it', async () => {
    listSettings.mockResolvedValue(payload())
    putSettings.mockResolvedValue(payload())
    render(<SettingsPage />)
    await screen.findByText('No operators.')

    fireEvent.click(screen.getByRole('button', { name: 'Add holiday' }))
    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Ferie' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(putSettings).toHaveBeenCalledTimes(1))
    const body = putSettings.mock.calls[0][0]
    expect(body.holidays[YEAR]).toEqual([
      { from: `${YEAR}-01-01`, to: `${YEAR}-01-01`, name: 'Ferie' },
    ])
  })

  it('shows the backend error when a save is rejected', async () => {
    listSettings.mockResolvedValue(payload())
    putSettings.mockRejectedValue(
      new Error('holidays.2026 ranges need a non-empty name'),
    )
    render(<SettingsPage />)
    await screen.findByText('No operators.')

    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(
      await screen.findByText('holidays.2026 ranges need a non-empty name'),
    ).toBeTruthy()
  })
})
