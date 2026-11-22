import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import WorkLogPage from './WorkLogPage'

const {
  getRepair,
  addWorkLog,
  updateWorkLog,
  listGasCylinders,
  getOperators,
  getRefrigerator,
  listRefrigerators,
} = vi.hoisted(() => ({
  getRepair: vi.fn(),
  addWorkLog: vi.fn(),
  updateWorkLog: vi.fn(),
  listGasCylinders: vi.fn(),
  getOperators: vi.fn(),
  getRefrigerator: vi.fn(),
  listRefrigerators: vi.fn(),
}))

vi.mock('../api/repairs', () => ({ getRepair, addWorkLog, updateWorkLog }))
vi.mock('../api/equipment', () => ({
  listGasCylinders,
  getRefrigerator,
  listRefrigerators,
}))
vi.mock('../api/settings', () => ({ getOperators }))

beforeEach(() => {
  getOperators.mockResolvedValue(['FABRI', 'CLAUDIO', 'MARIO', 'LUIGI'])
  listGasCylinders.mockResolvedValue([{ id: 7, gas_kind: 'R32' }])
  listRefrigerators.mockResolvedValue([
    { id: 3, serial_nr: 'FR-3', gas_kind: 'R32', gas_kg: 3, allestimento_id: 5 },
  ])
})

afterEach(() => {
  cleanup()
  vi.resetAllMocks()
})

const baseRepair = {
  id: 1,
  customer: 9,
  customer_name: 'ACME',
  vehicle: 5,
  gas_equipment_locked: false,
  refrigerator_installed: null,
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
      gas_operation: null,
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

async function chooseOperation(name: string) {
  const select = screen.getByRole('combobox', { name: 'Gas operation' })
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

  it('records a fill operation with the added amount', async () => {
    getRepair.mockResolvedValue(baseRepair)
    addWorkLog.mockResolvedValue({ id: 20 })
    renderAt('/repairs/1/work-log/new')

    await screen.findByText('New work log')
    await chooseOperator('FABRI')
    await chooseOperation('Fill')
    fireEvent.click(screen.getByRole('button', { name: 'Search' }))
    fireEvent.click(await screen.findByText('R32 #7'))
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())

    fireEvent.change(screen.getByLabelText('Added gas (kg)'), {
      target: { value: '2.5' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(addWorkLog).toHaveBeenCalled())
    expect(addWorkLog.mock.calls[0][1]).toMatchObject({
      operator: 'FABRI',
      gas_operation: 'fill',
      gas_recharge: 7,
      gas_measured_kg: 2.5,
      expected_refrigerator: 3,
    })
  })

  it('previews the calculated recovery for a combined operation', async () => {
    getRepair.mockResolvedValue(baseRepair)
    renderAt('/repairs/1/work-log/new')

    await screen.findByText('New work log')
    await chooseOperation('Recovery + recharge')
    fireEvent.change(screen.getByLabelText('Net added gas (kg)'), {
      target: { value: '0.4' },
    })

    expect(screen.getByText(/Recovered \(calculated\): 2.6 kg/)).toBeTruthy()
  })

  it('offers only cylinders matching the refrigerator gas type', async () => {
    getRepair.mockResolvedValue(baseRepair)
    listGasCylinders.mockResolvedValue([
      { id: 7, gas_kind: 'R32' },
      { id: 8, gas_kind: 'R410A' },
    ])
    renderAt('/repairs/1/work-log/new')

    await screen.findByText('New work log')
    await chooseOperation('Recovery')
    fireEvent.click(screen.getByRole('button', { name: 'Search' }))

    expect(await screen.findByText('R32 #7')).toBeTruthy()
    expect(screen.queryByText('R410A #8')).toBeNull()
  })

  it('blocks a gas operation when no refrigerator is installed', async () => {
    getRepair.mockResolvedValue(baseRepair)
    listRefrigerators.mockResolvedValue([])
    renderAt('/repairs/1/work-log/new')

    await screen.findByText('New work log')
    await chooseOperation('Fill')

    expect(
      await screen.findByText(/No refrigerator is installed/),
    ).toBeTruthy()
    expect(
      (screen.getByRole('button', { name: 'Save' }) as HTMLButtonElement).disabled,
    ).toBe(true)
  })

  it('blocks a gas operation when the locked refrigerator was replaced', async () => {
    getRepair.mockResolvedValue({
      ...baseRepair,
      gas_equipment_locked: true,
      refrigerator: 3,
      refrigerator_installed: false,
    })
    getRefrigerator.mockResolvedValue({
      id: 3,
      serial_nr: 'FR-3',
      gas_kind: 'R32',
      gas_kg: 3,
    })
    renderAt('/repairs/1/work-log/new')

    await screen.findByText('New work log')
    await chooseOperation('Recovery')

    expect(
      await screen.findByText(/replaced on its allestimento/),
    ).toBeTruthy()
  })

  it('reverses a saved gas operation when switching it to None', async () => {
    getRepair.mockResolvedValue({
      ...baseRepair,
      work_log: [
        {
          ...baseRepair.work_log[0],
          gas_operation: 'fill',
          gas_recharge: 7,
          gas_measured_kg: 2.5,
        },
      ],
    })
    updateWorkLog.mockResolvedValue({ id: 10 })
    renderAt('/repairs/1/work-log/10')

    await screen.findByLabelText('Added gas (kg)')
    await chooseOperation('None')
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(updateWorkLog).toHaveBeenCalled())
    expect(updateWorkLog.mock.calls[0][2]).toMatchObject({ gas_operation: 'none' })
  })

  it('leaves the stored gas dataset unchanged on a metadata edit', async () => {
    getRepair.mockResolvedValue({
      ...baseRepair,
      work_log: [
        {
          ...baseRepair.work_log[0],
          description: 'Filtro',
          gas_operation: 'fill',
          gas_recharge: 7,
          gas_measured_kg: 2.5,
        },
      ],
    })
    updateWorkLog.mockResolvedValue({ id: 10 })
    renderAt('/repairs/1/work-log/10')

    const description = await screen.findByDisplayValue('Filtro')
    fireEvent.change(description, { target: { value: 'Filtro nuovo' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(updateWorkLog).toHaveBeenCalled())
    const body = updateWorkLog.mock.calls[0][2]
    expect(body.description).toBe('Filtro nuovo')
    expect(body.gas_operation).toBeUndefined()
    expect(body.gas_recharge).toBeUndefined()
  })
})
