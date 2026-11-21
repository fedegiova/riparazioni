import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { ApiError } from '../api/client'
import CylinderPage from './CylinderPage'

const { getGasCylinder, getCylinderOperations } = vi.hoisted(() => ({
  getGasCylinder: vi.fn(),
  getCylinderOperations: vi.fn(),
}))

vi.mock('../api/equipment', () => ({ getGasCylinder, getCylinderOperations }))

afterEach(() => {
  cleanup()
  vi.resetAllMocks()
})

function renderPage(id = '7') {
  return render(
    <MemoryRouter initialEntries={[`/magazzino/bombole/${id}`]}>
      <Routes>
        <Route path="/magazzino/bombole/:id" element={<CylinderPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('CylinderPage', () => {
  it('shows the cylinder state and its operations with references', async () => {
    getGasCylinder.mockResolvedValue({
      id: 7,
      serial_nr: 'CYL-7',
      gas_kind: 'R134a',
      model: 'M1',
      full_weight: 10,
      remaining_weight: 4,
      archived: false,
    })
    getCylinderOperations.mockResolvedValue([
      {
        kind: 'recharge',
        date: '2026-03-01T09:00:00',
        repair_id: 12,
        work_log_id: 34,
        operator: 'Mario',
        recharged_weight: 2.5,
        remaining_weight: 7.5,
      },
      {
        kind: 'refill',
        id: 1,
        date: '2026-02-01',
        reference: 'Supplier X',
        remaining_weight: 10,
      },
    ])
    renderPage()

    expect(await screen.findByText('Bombola CYL-7')).toBeTruthy()
    expect(screen.getByText('Gas: R134a')).toBeTruthy()
    expect(screen.getByText(/4 \/ 10 kg/)).toBeTruthy()
    expect(screen.getByText('Active')).toBeTruthy()
    expect(screen.getByText('Recharge')).toBeTruthy()
    expect(screen.getByText('Recharged 2.5 kg')).toBeTruthy()
    expect(screen.getByText('7.5 kg')).toBeTruthy()
    expect(screen.getByText('Refill')).toBeTruthy()
    expect(screen.getByText('Supplier X')).toBeTruthy()

    const link = screen.getByRole('link', { name: 'Repair #12' })
    expect(link.getAttribute('href')).toBe('/repairs/12')
  })

  it('marks an archived cylinder as archived', async () => {
    getGasCylinder.mockResolvedValue({
      id: 7,
      serial_nr: 'CYL-7',
      full_weight: 10,
      remaining_weight: 1,
      archived: true,
    })
    getCylinderOperations.mockResolvedValue([])
    renderPage()

    expect(await screen.findByText('Archived')).toBeTruthy()
    expect(screen.getByText('No operations.')).toBeTruthy()
  })

  it('reports an error instead of an empty list', async () => {
    getGasCylinder.mockResolvedValue({ id: 7, full_weight: 10 })
    getCylinderOperations.mockRejectedValue(new ApiError(500, 'Boom'))
    renderPage()

    expect(await screen.findByRole('alert')).toBeTruthy()
    expect(screen.getByText('Boom')).toBeTruthy()
    expect(screen.queryByText('No operations.')).toBeNull()
  })
})
