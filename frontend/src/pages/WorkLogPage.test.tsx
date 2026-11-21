import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import WorkLogPage from './WorkLogPage'

const { getRepair, addWorkLog, updateWorkLog, listGasCylinders } = vi.hoisted(
  () => ({
    getRepair: vi.fn(),
    addWorkLog: vi.fn(),
    updateWorkLog: vi.fn(),
    listGasCylinders: vi.fn(),
  }),
)

vi.mock('../api/repairs', () => ({ getRepair, addWorkLog, updateWorkLog }))
vi.mock('../api/equipment', () => ({ listGasCylinders }))

afterEach(() => {
  cleanup()
  vi.resetAllMocks()
})

const baseRepair = {
  id: 1,
  customer: 9,
  customer_name: 'ACME',
  start_data: '2026-11-01T08:00:00',
  end_data: null,
  total_hours: 1,
  work_log: [
    {
      id: 10,
      start_time: '2026-11-01T09:00:00',
      end_time: '2026-11-01T10:00:00',
      operator: 'LORENZA',
    },
  ],
}

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route
          path="/repairs/:id/work-log/:entryId"
          element={<WorkLogPage />}
        />
        <Route path="/repairs/:id" element={<div>repair page</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('WorkLogPage', () => {
  it('updates the entry time and operator', async () => {
    getRepair.mockResolvedValue(baseRepair)
    updateWorkLog.mockResolvedValue({ id: 10 })
    renderAt('/repairs/1/work-log/10')

    const operator = await screen.findByDisplayValue('LORENZA')
    fireEvent.change(operator, { target: { value: 'MARIO' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(updateWorkLog).toHaveBeenCalled())
    expect(updateWorkLog.mock.calls[0][0]).toBe(1)
    expect(updateWorkLog.mock.calls[0][1]).toBe(10)
    expect(updateWorkLog.mock.calls[0][2]).toMatchObject({ operator: 'MARIO' })
  })

  it('prefills the start time for a new entry', async () => {
    getRepair.mockResolvedValue(baseRepair)
    renderAt('/repairs/1/work-log/new')

    await screen.findByText('New work log')
    const start = screen.getByLabelText('Start time') as HTMLInputElement
    expect(start.value).not.toBe('')
  })

  it('captures a gas recharge on a new entry', async () => {
    getRepair.mockResolvedValue(baseRepair)
    addWorkLog.mockResolvedValue({ id: 20 })
    listGasCylinders.mockResolvedValue([{ id: 7, gas_kind: 'R134a' }])
    renderAt('/repairs/1/work-log/new')

    await screen.findByText('New work log')
    fireEvent.click(screen.getByRole('button', { name: 'Add gas recharge' }))

    fireEvent.mouseDown(
      screen.getByRole('combobox', { name: 'Gas system state' }),
    )
    fireEvent.click(await screen.findByRole('option', { name: 'VUOTO' }))

    fireEvent.click(screen.getByRole('button', { name: 'Search' }))
    fireEvent.click(await screen.findByText('R134a #7'))
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())

    fireEvent.change(screen.getByLabelText('Recharge weight (kg)'), {
      target: { value: '2.5' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(addWorkLog).toHaveBeenCalled())
    expect(addWorkLog.mock.calls[0][1]).toMatchObject({
      gas_system_state: 'VUOTO',
      gas_recharge: 7,
      gas_recharge_weight: 2.5,
    })
  })
})
