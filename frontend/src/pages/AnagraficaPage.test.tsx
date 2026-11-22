import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import AnagraficaPage from './AnagraficaPage'
import { ApiError } from '../api/client'

const {
  listCustomers,
  listVehicles,
  listRefrigerators,
  createRefrigerator,
  updateRefrigerator,
  installRefrigerator,
  getGasTypes,
} = vi.hoisted(() => ({
  listCustomers: vi.fn(),
  listVehicles: vi.fn(),
  listRefrigerators: vi.fn(),
  createRefrigerator: vi.fn(),
  updateRefrigerator: vi.fn(),
  installRefrigerator: vi.fn(),
  getGasTypes: vi.fn(),
}))

vi.mock('../api/reference', () => ({ listCustomers, listVehicles }))
vi.mock('../api/equipment', () => ({
  listRefrigerators,
  createRefrigerator,
  updateRefrigerator,
  installRefrigerator,
}))
vi.mock('../api/settings', () => ({ getGasTypes }))

beforeEach(() => {
  getGasTypes.mockResolvedValue(['R32', 'R410A'])
  listRefrigerators.mockResolvedValue([])
})

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

const rossi = {
  id: 1,
  cliente: 'Rossi S.p.A.',
  via: 'Via Roma 1',
  cap: '20100',
  citta: 'Milano',
  prov: 'MI',
  tel: '0212345678',
  cell: '3331234567',
  email: 'info@rossi.it',
}
const bianchi = {
  id: 2,
  cliente: 'Bianchi S.r.l.',
  via: 'Corso Torino 5',
  cap: '10100',
  citta: 'Torino',
  prov: 'TO',
  tel: '0119876543',
  cell: '3477654321',
  email: 'info@bianchi.it',
}
const daily = {
  id: 1,
  targa: 'AB123CD',
  autocarro: 'Iveco Daily',
  carrozzeria: 'Furgone',
  modello: 'Daily',
  classe: 'N1',
  commessa: 'C-001',
}
const ducato = {
  id: 2,
  targa: 'EF456GH',
  autocarro: 'Fiat Ducato',
  carrozzeria: 'Cassonato',
  modello: 'Ducato',
  classe: 'N1',
  commessa: 'C-002',
}

function renderPage() {
  return render(<AnagraficaPage />)
}

describe('AnagraficaPage', () => {
  it('shows the two tabs with Clienti selected and lists customers', async () => {
    listCustomers.mockResolvedValue([rossi])
    renderPage()

    expect(screen.getByRole('tab', { name: 'Clienti' })).toBeTruthy()
    expect(screen.getByRole('tab', { name: 'Allestimenti' })).toBeTruthy()
    expect(
      screen.getByRole('tab', { name: 'Clienti' }).getAttribute('aria-selected'),
    ).toBe('true')
    expect(await screen.findByText('Rossi S.p.A.')).toBeTruthy()
  })

  it('lists allestimenti after switching to the Allestimenti tab', async () => {
    listCustomers.mockResolvedValue([])
    listVehicles.mockResolvedValue([daily])
    renderPage()

    fireEvent.click(screen.getByRole('tab', { name: 'Allestimenti' }))

    expect(await screen.findByText('AB123CD')).toBeTruthy()
    expect(listVehicles).toHaveBeenCalled()
  })

  it('reports a customer load failure', async () => {
    listCustomers.mockRejectedValue(new ApiError(500, 'customers unavailable'))
    renderPage()

    expect(await screen.findByText('customers unavailable')).toBeTruthy()
  })

  it('reports an allestimenti load failure', async () => {
    listCustomers.mockResolvedValue([])
    listVehicles.mockRejectedValue(new ApiError(500, 'vehicles unavailable'))
    renderPage()

    fireEvent.click(screen.getByRole('tab', { name: 'Allestimenti' }))

    expect(await screen.findByText('vehicles unavailable')).toBeTruthy()
  })

  it('filters the customer list with the search box', async () => {
    listCustomers.mockResolvedValue([rossi, bianchi])
    renderPage()

    await screen.findByText('Rossi S.p.A.')
    expect(screen.getByText('Bianchi S.r.l.')).toBeTruthy()

    fireEvent.change(screen.getByLabelText('Search'), {
      target: { value: 'torino' },
    })
    expect(screen.queryByText('Rossi S.p.A.')).toBeNull()
    expect(screen.getByText('Bianchi S.r.l.')).toBeTruthy()

    fireEvent.change(screen.getByLabelText('Search'), { target: { value: '' } })
    expect(screen.getByText('Rossi S.p.A.')).toBeTruthy()

    fireEvent.change(screen.getByLabelText('Search'), {
      target: { value: 'zzz' },
    })
    expect(screen.queryByText('Rossi S.p.A.')).toBeNull()
    expect(screen.queryByText('Bianchi S.r.l.')).toBeNull()
    expect(screen.getByText('No matches.')).toBeTruthy()
  })

  it('filters the allestimenti list with the search box', async () => {
    listCustomers.mockResolvedValue([])
    listVehicles.mockResolvedValue([daily, ducato])
    renderPage()

    fireEvent.click(screen.getByRole('tab', { name: 'Allestimenti' }))
    await screen.findByText('AB123CD')
    expect(screen.getByText('EF456GH')).toBeTruthy()

    fireEvent.change(screen.getByLabelText('Search'), {
      target: { value: 'ducato' },
    })
    expect(screen.queryByText('AB123CD')).toBeNull()
    expect(screen.getByText('EF456GH')).toBeTruthy()
  })

  it('keeps the legacy vehicle and customer records read-only', async () => {
    listCustomers.mockResolvedValue([rossi])
    listVehicles.mockResolvedValue([daily])
    renderPage()

    await screen.findByText('Rossi S.p.A.')
    // The Clienti tab offers no write control at all.
    expect(
      screen.queryByRole('button', { name: /create|new|edit|delete|save/i }),
    ).toBeNull()

    fireEvent.click(screen.getByRole('tab', { name: 'Allestimenti' }))
    await screen.findByText('AB123CD')
    // Only the app-owned refrigerator can be managed; the vehicle is not.
    expect(
      screen.queryByRole('button', {
        name: /edit vehicle|delete vehicle|new vehicle|edit allestimento/i,
      }),
    ).toBeNull()
    expect(
      screen.getByRole('button', { name: 'Add refrigerator for AB123CD' }),
    ).toBeTruthy()
  })

  it('shows the installed refrigerator for a vehicle', async () => {
    listCustomers.mockResolvedValue([])
    listVehicles.mockResolvedValue([daily])
    listRefrigerators.mockResolvedValue([
      { id: 5, serial_nr: 'FR-1', gas_kind: 'R32', gas_kg: 3, allestimento_id: 1 },
    ])
    renderPage()

    fireEvent.click(screen.getByRole('tab', { name: 'Allestimenti' }))

    expect(await screen.findByText(/FR-1/)).toBeTruthy()
    expect(screen.getByText('R32')).toBeTruthy()
    expect(
      screen.queryByRole('button', { name: 'Add refrigerator for AB123CD' }),
    ).toBeNull()
    expect(
      screen.getByRole('button', { name: 'Edit refrigerator for AB123CD' }),
    ).toBeTruthy()
    expect(
      screen.getByRole('button', { name: 'Replace refrigerator for AB123CD' }),
    ).toBeTruthy()
  })

  it('adds a refrigerator to an allestimento with none installed', async () => {
    listCustomers.mockResolvedValue([])
    listVehicles.mockResolvedValue([daily])
    listRefrigerators
      .mockResolvedValueOnce([])
      .mockResolvedValue([
        { id: 9, serial_nr: 'FR-9', gas_kind: 'R32', gas_kg: 3, allestimento_id: 1 },
      ])
    createRefrigerator.mockResolvedValue({ id: 9 })
    renderPage()

    fireEvent.click(screen.getByRole('tab', { name: 'Allestimenti' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Add refrigerator for AB123CD' }))

    fireEvent.change(screen.getByLabelText('Serial number'), { target: { value: 'FR-9' } })
    fireEvent.change(screen.getByLabelText('Manufacturer'), { target: { value: 'B' } })
    fireEvent.change(screen.getByLabelText('Model'), { target: { value: 'M' } })
    fireEvent.change(screen.getByLabelText('Gas type'), { target: { value: 'R32' } })
    fireEvent.change(screen.getByLabelText(/Nameplate capacity/), {
      target: { value: '3' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(createRefrigerator).toHaveBeenCalled())
    expect(createRefrigerator.mock.calls[0][0]).toMatchObject({
      serial_nr: 'FR-9',
      brand: 'B',
      model: 'M',
      gas_kind: 'R32',
      gas_kg: 3,
      allestimento_id: 1,
    })
    // The row refreshes with the saved unit.
    expect(await screen.findByText(/FR-9/)).toBeTruthy()
  })

  it('edits an installed refrigerator', async () => {
    listCustomers.mockResolvedValue([])
    listVehicles.mockResolvedValue([daily])
    listRefrigerators.mockResolvedValue([
      { id: 5, serial_nr: 'FR-1', brand: 'B', model: 'OLD', gas_kind: 'R32', gas_kg: 3, allestimento_id: 1 },
    ])
    updateRefrigerator.mockResolvedValue({ id: 5 })
    renderPage()

    fireEvent.click(screen.getByRole('tab', { name: 'Allestimenti' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Edit refrigerator for AB123CD' }))

    fireEvent.change(screen.getByLabelText('Model'), { target: { value: 'NEW' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(updateRefrigerator).toHaveBeenCalled())
    expect(updateRefrigerator.mock.calls[0][0]).toBe(5)
    expect(updateRefrigerator.mock.calls[0][1]).toMatchObject({ model: 'NEW' })
  })

  it('replaces the installed refrigerator explicitly', async () => {
    listCustomers.mockResolvedValue([])
    listVehicles.mockResolvedValue([daily])
    listRefrigerators.mockResolvedValue([
      { id: 5, serial_nr: 'FR-1', brand: 'B', model: 'M', gas_kind: 'R32', gas_kg: 3, allestimento_id: 1 },
    ])
    createRefrigerator.mockResolvedValue({ id: 12 })
    installRefrigerator.mockResolvedValue({ id: 12 })
    renderPage()

    fireEvent.click(screen.getByRole('tab', { name: 'Allestimenti' }))
    fireEvent.click(
      await screen.findByRole('button', { name: 'Replace refrigerator for AB123CD' }),
    )

    fireEvent.change(screen.getByLabelText('Serial number'), { target: { value: 'FR-NEW' } })
    fireEvent.change(screen.getByLabelText('Manufacturer'), { target: { value: 'B' } })
    fireEvent.change(screen.getByLabelText('Model'), { target: { value: 'M' } })
    fireEvent.change(screen.getByLabelText('Gas type'), { target: { value: 'R32' } })
    fireEvent.change(screen.getByLabelText(/Nameplate capacity/), {
      target: { value: '3' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(installRefrigerator).toHaveBeenCalledWith(12, 1))
    expect(createRefrigerator).toHaveBeenCalled()
  })

  it('reports a rejected refrigerator save', async () => {
    listCustomers.mockResolvedValue([])
    listVehicles.mockResolvedValue([daily])
    listRefrigerators.mockResolvedValue([])
    createRefrigerator.mockRejectedValue(new ApiError(409, 'already installed'))
    renderPage()

    fireEvent.click(screen.getByRole('tab', { name: 'Allestimenti' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Add refrigerator for AB123CD' }))

    fireEvent.change(screen.getByLabelText('Serial number'), { target: { value: 'FR-9' } })
    fireEvent.change(screen.getByLabelText('Manufacturer'), { target: { value: 'B' } })
    fireEvent.change(screen.getByLabelText('Model'), { target: { value: 'M' } })
    fireEvent.change(screen.getByLabelText('Gas type'), { target: { value: 'R32' } })
    fireEvent.change(screen.getByLabelText(/Nameplate capacity/), {
      target: { value: '3' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(await screen.findByText('already installed')).toBeTruthy()
  })
})
