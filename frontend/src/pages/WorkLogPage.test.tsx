import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import WorkLogPage from './WorkLogPage'

const { getRepair, addWorkLog, updateWorkLog, listGasCylinders, getOperators } =
  vi.hoisted(() => ({
    getRepair: vi.fn(),
    addWorkLog: vi.fn(),
    updateWorkLog: vi.fn(),
    listGasCylinders: vi.fn(),
    getOperators: vi.fn(),
  }))

vi.mock('../api/repairs', () => ({ getRepair, addWorkLog, updateWorkLog }))
vi.mock('../api/equipment', () => ({ listGasCylinders }))
vi.mock('../api/settings', () => ({ getOperators }))

beforeEach(() => {
  getOperators.mockResolvedValue(['FABRI', 'CLAUDIO', 'MARIO', 'LUIGI'])
})

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
      description: null,
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

async function chooseOperator(name: string) {
  const select = await screen.findByRole('combobox', { name: 'Operator' })
  fireEvent.mouseDown(select)
  fireEvent.click(await screen.findByRole('option', { name }))
}

describe('WorkLogPage', () => {
  it('updates the entry time and operator', async () => {
    getRepair.mockResolvedValue(baseRepair)
    updateWorkLog.mockResolvedValue({ id: 10 })
    renderAt('/repairs/1/work-log/10')

    await chooseOperator('MARIO')
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(updateWorkLog).toHaveBeenCalled())
    expect(updateWorkLog.mock.calls[0][0]).toBe(1)
    expect(updateWorkLog.mock.calls[0][1]).toBe(10)
    expect(updateWorkLog.mock.calls[0][2]).toMatchObject({ operator: 'MARIO' })
  })

  it('sends the entered times as local wall-clock time', async () => {
    getRepair.mockResolvedValue(baseRepair)
    updateWorkLog.mockResolvedValue({ id: 10 })
    renderAt('/repairs/1/work-log/10')

    await screen.findByLabelText('Start time')
    fireEvent.change(screen.getByLabelText('Start time'), {
      target: { value: '2026-11-22T00:13' },
    })
    fireEvent.change(screen.getByLabelText('End time'), {
      target: { value: '2026-11-22T01:43' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(updateWorkLog).toHaveBeenCalled())
    expect(updateWorkLog.mock.calls[0][2]).toMatchObject({
      start_time: '2026-11-22T00:13:00',
      end_time: '2026-11-22T01:43:00',
    })
  })

  it('prefills the start time for a new entry', async () => {
    getRepair.mockResolvedValue(baseRepair)
    renderAt('/repairs/1/work-log/new')

    await screen.findByText('New work log')
    const start = screen.getByLabelText('Start time') as HTMLInputElement
    expect(start.value).not.toBe('')
  })

  it('selects an operator from the configured list', async () => {
    getRepair.mockResolvedValue(baseRepair)
    getOperators.mockResolvedValue(['MARIO', 'LUIGI'])
    updateWorkLog.mockResolvedValue({ id: 10 })
    renderAt('/repairs/1/work-log/10')

    await chooseOperator('MARIO')
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(updateWorkLog).toHaveBeenCalled())
    expect(updateWorkLog.mock.calls[0][2]).toMatchObject({ operator: 'MARIO' })
  })

  it('keeps the current operator when it is not in settings', async () => {
    getRepair.mockResolvedValue(baseRepair)
    getOperators.mockResolvedValue(['MARIO'])
    renderAt('/repairs/1/work-log/10')

    const select = await screen.findByRole('combobox', { name: 'Operator' })
    expect(select.textContent).toContain('LORENZA')
    fireEvent.mouseDown(select)
    expect(await screen.findByRole('option', { name: 'LORENZA' })).toBeTruthy()
  })

  it('keeps the operator optional when editing an existing entry', async () => {
    getRepair.mockResolvedValue(baseRepair)
    getOperators.mockResolvedValue(['MARIO'])
    updateWorkLog.mockResolvedValue({ id: 10 })
    renderAt('/repairs/1/work-log/10')

    await chooseOperator('None')
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(updateWorkLog).toHaveBeenCalled())
    expect(updateWorkLog.mock.calls[0][2].operator).toBeUndefined()
  })

  it('prefills the description and submits changes', async () => {
    getRepair.mockResolvedValue({
      ...baseRepair,
      work_log: [{ ...baseRepair.work_log[0], description: 'Filtro' }],
    })
    updateWorkLog.mockResolvedValue({ id: 10 })
    renderAt('/repairs/1/work-log/10')

    const description = await screen.findByDisplayValue('Filtro')
    fireEvent.change(description, { target: { value: 'Filtro e guarnizione' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(updateWorkLog).toHaveBeenCalled())
    expect(updateWorkLog.mock.calls[0][2]).toMatchObject({
      description: 'Filtro e guarnizione',
    })
  })

  it('requires an operator before creating an entry', async () => {
    getRepair.mockResolvedValue(baseRepair)
    renderAt('/repairs/1/work-log/new')

    const save = (await screen.findByRole('button', {
      name: 'Save',
    })) as HTMLButtonElement
    expect(save.disabled).toBe(true)

    await chooseOperator('FABRI')
    expect(save.disabled).toBe(false)
  })

  it('explains when no operators are configured for a new entry', async () => {
    getRepair.mockResolvedValue(baseRepair)
    getOperators.mockResolvedValue([])
    renderAt('/repairs/1/work-log/new')

    expect(await screen.findByText(/No operators are configured/)).toBeTruthy()
    const save = screen.getByRole('button', { name: 'Save' }) as HTMLButtonElement
    expect(save.disabled).toBe(true)
    expect(screen.queryByRole('textbox', { name: 'Operator' })).toBeNull()
  })

  it('captures a gas recharge on a new entry', async () => {
    getRepair.mockResolvedValue(baseRepair)
    addWorkLog.mockResolvedValue({ id: 20 })
    listGasCylinders.mockResolvedValue([{ id: 7, gas_kind: 'R134a' }])
    renderAt('/repairs/1/work-log/new')

    await screen.findByText('New work log')
    await chooseOperator('FABRI')
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
      operator: 'FABRI',
      gas_system_state: 'VUOTO',
      gas_recharge: 7,
      gas_recharge_weight: 2.5,
    })
  })
})