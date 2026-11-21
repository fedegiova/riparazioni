import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import RepairsListPage from './RepairsListPage'

const { listRepairs, deleteRepair, repairsExportUrl, downloadUrl } = vi.hoisted(
  () => ({
    listRepairs: vi.fn(),
    deleteRepair: vi.fn(),
    repairsExportUrl: vi.fn(() => '/api/v1/repairs/export?customer=9'),
    downloadUrl: vi.fn(),
  }),
)
vi.mock('../api/repairs', () => ({
  listRepairs,
  deleteRepair,
  repairsExportUrl,
}))
vi.mock('../lib/download', () => ({ downloadUrl }))

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

const active = {
  id: 1,
  customer_name: 'ACME',
  total_hours: 2,
  start_data: '2026-11-01T08:00:00',
  end_data: null,
  delivery_date: '2026-11-10',
}
const completed = {
  id: 2,
  customer_name: 'Beta',
  total_hours: 3,
  start_data: '2026-10-01T08:00:00',
  end_data: '2026-10-05T16:00:00',
  delivery_date: null,
}

function renderPage() {
  return render(
    <MemoryRouter>
      <RepairsListPage />
    </MemoryRouter>,
  )
}

describe('RepairsListPage', () => {
  it('lists completed repairs and narrows when a filter is applied', async () => {
    listRepairs.mockResolvedValueOnce([active, completed]).mockResolvedValueOnce([active])
    renderPage()

    expect(await screen.findByText('ACME')).toBeTruthy()
    expect(screen.getByText('Beta')).toBeTruthy()

    fireEvent.change(screen.getByLabelText('Customer id'), {
      target: { value: '9' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Apply' }))

    await waitFor(() =>
      expect(listRepairs).toHaveBeenLastCalledWith(
        expect.objectContaining({ customer: 9 }),
      ),
    )
    await waitFor(() => expect(screen.queryByText('Beta')).toBeNull())
  })

  it('deletes a repair only after confirmation', async () => {
    listRepairs.mockResolvedValue([active])
    deleteRepair.mockResolvedValue(undefined)
    renderPage()

    await screen.findByText('ACME')
    fireEvent.click(screen.getByRole('button', { name: 'Delete repair 1' }))
    expect(screen.getByText(/Delete repair #1/)).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    expect(deleteRepair).not.toHaveBeenCalled()

    fireEvent.click(screen.getByRole('button', { name: 'Delete repair 1' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Delete' }))
    await waitFor(() => expect(deleteRepair).toHaveBeenCalledWith(1))
  })

  it('exports using the applied filter', async () => {
    listRepairs.mockResolvedValue([active])
    renderPage()

    await screen.findByText('ACME')
    fireEvent.change(screen.getByLabelText('Customer id'), {
      target: { value: '9' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Apply' }))
    await waitFor(() => expect(listRepairs).toHaveBeenCalledTimes(2))

    fireEvent.click(screen.getByRole('button', { name: 'Export XLSX' }))
    expect(repairsExportUrl).toHaveBeenLastCalledWith(
      expect.objectContaining({ customer: 9 }),
    )
    expect(downloadUrl).toHaveBeenCalledWith(
      '/api/v1/repairs/export?customer=9',
      'repairs.xlsx',
    )
  })
})
