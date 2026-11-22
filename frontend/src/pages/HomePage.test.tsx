import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes, useParams } from 'react-router-dom'
import HomePage from './HomePage'

const { listRepairs } = vi.hoisted(() => ({ listRepairs: vi.fn() }))
vi.mock('../api/repairs', () => ({ listRepairs }))

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

function WorkLogStub() {
  const { entryId } = useParams()
  return <div>work log {entryId}</div>
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/repairs/new" element={<div>new repair page</div>} />
        <Route path="/repairs/:id" element={<div>repair detail page</div>} />
        <Route
          path="/repairs/:id/work-log/:entryId"
          element={<WorkLogStub />}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe('HomePage', () => {
  it('shows only active repairs and opens one', async () => {
    listRepairs.mockResolvedValue([
      {
        id: 1,
        customer_name: 'ACME',
        total_hours: 4.5,
        start_data: '2026-11-01T08:00:00',
        end_data: null,
        delivery_date: '2026-11-12',
      },
      {
        id: 2,
        customer_name: 'Beta',
        total_hours: 1,
        start_data: '2026-10-01T08:00:00',
        end_data: '2026-10-05T16:00:00',
        delivery_date: null,
      },
    ])

    renderPage()

    expect(await screen.findByText('ACME')).toBeTruthy()
    expect(screen.queryByText('Beta')).toBeNull()
    expect(screen.getByText('4h 30m')).toBeTruthy()
    expect(screen.getByRole('columnheader', { name: 'Delivery date' })).toBeTruthy()
    expect(screen.getByText('2026-11-12')).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: 'Open repair 1' }))
    expect(await screen.findByText('repair detail page')).toBeTruthy()
  })

  it('opens the new-repair page from the create control', async () => {
    listRepairs.mockResolvedValue([])
    renderPage()

    await screen.findByText('No active repairs.')
    fireEvent.click(screen.getByRole('button', { name: 'New repair' }))
    expect(await screen.findByText('new repair page')).toBeTruthy()
  })

  it('starts a work log from a repair row', async () => {
    listRepairs.mockResolvedValue([
      {
        id: 1,
        customer_name: 'ACME',
        total_hours: 0,
        start_data: '2026-11-01T08:00:00',
        end_data: null,
        delivery_date: null,
      },
    ])
    renderPage()

    await screen.findByText('ACME')
    fireEvent.click(screen.getByRole('button', { name: 'Start work log 1' }))
    expect(await screen.findByText('work log new')).toBeTruthy()
  })
})
