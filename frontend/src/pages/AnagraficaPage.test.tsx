import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import AnagraficaPage from './AnagraficaPage'
import { ApiError } from '../api/client'

const { listCustomers, listVehicles } = vi.hoisted(() => ({
  listCustomers: vi.fn(),
  listVehicles: vi.fn(),
}))

vi.mock('../api/reference', () => ({ listCustomers, listVehicles }))

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

  it('offers no create, edit, or delete controls', async () => {
    listCustomers.mockResolvedValue([rossi])
    listVehicles.mockResolvedValue([daily])
    renderPage()

    await screen.findByText('Rossi S.p.A.')
    expect(
      screen.queryByRole('button', { name: /create|new|edit|delete|save/i }),
    ).toBeNull()

    fireEvent.click(screen.getByRole('tab', { name: 'Allestimenti' }))
    await screen.findByText('AB123CD')
    expect(
      screen.queryByRole('button', { name: /create|new|edit|delete|save/i }),
    ).toBeNull()
  })
})
