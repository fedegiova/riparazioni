import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes, useParams } from 'react-router-dom'
import RepairPage from './RepairPage'

const {
  getRepair,
  createRepair,
  updateRepair,
  updateWorkLog,
  deleteWorkLog,
  listCustomers,
  listVehicles,
  listServiceParts,
  uploadPicture,
  deletePicture,
} = vi.hoisted(() => ({
  getRepair: vi.fn(),
  createRepair: vi.fn(),
  updateRepair: vi.fn(),
  updateWorkLog: vi.fn(),
  deleteWorkLog: vi.fn(),
  listCustomers: vi.fn(),
  listVehicles: vi.fn(),
  listServiceParts: vi.fn(),
  uploadPicture: vi.fn(),
  deletePicture: vi.fn(),
}))

vi.mock('../api/repairs', () => ({
  getRepair,
  createRepair,
  updateRepair,
  updateWorkLog,
  deleteWorkLog,
}))
vi.mock('../api/reference', () => ({ listCustomers, listVehicles }))
vi.mock('../api/equipment', () => ({ listServiceParts }))
vi.mock('../api/pictures', () => ({
  uploadPicture,
  deletePicture,
  pictureFileUrl: (id: number) => `/api/v1/pictures/${id}/file`,
}))

afterEach(() => {
  cleanup()
  vi.resetAllMocks()
})

const baseRepair = {
  id: 1,
  customer: 9,
  customer_name: 'ACME',
  vehicle: 5,
  start_data: '2026-11-01T08:00:00',
  end_data: null,
  delivery_date: '2026-11-12',
  total_hours: 2,
  notes: 'old',
  work_log: [
    {
      id: 10,
      start_time: '2026-11-01T09:00:00',
      end_time: '2026-11-01T10:00:00',
      operator: 'LORENZA',
    },
  ],
  parts: [],
}

function WorkLogStub() {
  const { entryId } = useParams()
  return <div>work log {entryId}</div>
}

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/repairs/new" element={<RepairPage />} />
        <Route path="/repairs/:id" element={<RepairPage />} />
        <Route
          path="/repairs/:id/work-log/:entryId"
          element={<WorkLogStub />}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe('RepairPage', () => {
  it('creates a new repair', async () => {
    getRepair.mockResolvedValue(null)
    createRepair.mockResolvedValue({ ...baseRepair, id: 42 })
    renderAt('/repairs/new')

    const notes = await screen.findByLabelText('Notes')
    fireEvent.change(notes, { target: { value: 'created' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(createRepair).toHaveBeenCalled())
    expect(createRepair.mock.calls[0][0]).toMatchObject({ notes: 'created' })
  })

  it('edits an existing repair', async () => {
    getRepair.mockResolvedValue(baseRepair)
    updateRepair.mockResolvedValue(baseRepair)
    renderAt('/repairs/1')

    const notes = await screen.findByDisplayValue('old')
    fireEvent.change(notes, { target: { value: 'updated' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(updateRepair).toHaveBeenCalled())
    expect(updateRepair.mock.calls[0][0]).toBe(1)
    expect(updateRepair.mock.calls[0][1]).toMatchObject({ notes: 'updated' })
  })

  it('picks a customer through the search modal', async () => {
    getRepair.mockResolvedValue({
      ...baseRepair,
      customer: null,
      customer_name: null,
    })
    updateRepair.mockResolvedValue(baseRepair)
    listCustomers.mockResolvedValue([{ id: 9, cliente: 'ACME', citta: 'Roma' }])
    renderAt('/repairs/1')

    await screen.findByDisplayValue('old')
    fireEvent.click(screen.getAllByRole('button', { name: 'Search' })[0])
    fireEvent.click(await screen.findByText('ACME'))
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    expect(screen.getByDisplayValue('ACME')).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(updateRepair).toHaveBeenCalled())
    expect(updateRepair.mock.calls[0][1]).toMatchObject({ customer: 9 })
  })

  it('adds a part and saves the full parts array', async () => {
    getRepair.mockResolvedValue(baseRepair)
    updateRepair.mockResolvedValue(baseRepair)
    listServiceParts.mockResolvedValue([
      { id: 3, name: 'Filter', price: 10, kind: 'consumable' },
    ])
    renderAt('/repairs/1')

    await screen.findByText('LORENZA')
    fireEvent.click(screen.getByRole('button', { name: 'Add part' }))
    fireEvent.click(await screen.findByText('Filter'))
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(updateRepair).toHaveBeenCalled())
    expect(updateRepair.mock.calls.at(-1)?.[1]).toMatchObject({
      parts: [{ id_part: 3, quantity: 1, unit_price: 10 }],
    })
  })

  it('deletes a part and saves the full parts array', async () => {
    getRepair.mockResolvedValue({
      ...baseRepair,
      parts: [
        {
          id: 1,
          id_part: 3,
          quantity: 2,
          unit_price: 10,
          part: { id: 3, name: 'Filter', price: 10 },
        },
      ],
    })
    updateRepair.mockResolvedValue(baseRepair)
    renderAt('/repairs/1')

    await screen.findByText('Filter')
    fireEvent.click(screen.getByRole('button', { name: 'Delete part Filter' }))
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(updateRepair).toHaveBeenCalled())
    expect(updateRepair.mock.calls.at(-1)?.[1]).toMatchObject({ parts: [] })
  })

  it('cancels and edits a work-log entry', async () => {
    getRepair.mockResolvedValue(baseRepair)
    deleteWorkLog.mockResolvedValue(undefined)
    renderAt('/repairs/1')

    await screen.findByText('LORENZA')
    fireEvent.click(screen.getByRole('button', { name: 'Cancel work log 10' }))
    await waitFor(() => expect(deleteWorkLog).toHaveBeenCalledWith(1, 10))

    fireEvent.click(screen.getByRole('button', { name: 'Edit work log 10' }))
    expect(await screen.findByText('work log 10')).toBeTruthy()
  })

  it('navigates to a new work-log page', async () => {
    getRepair.mockResolvedValue(baseRepair)
    renderAt('/repairs/1')

    await screen.findByText('LORENZA')
    fireEvent.click(screen.getByRole('button', { name: 'Add work log' }))
    expect(await screen.findByText('work log new')).toBeTruthy()
  })

  it('archives a repair by setting its end date', async () => {
    getRepair.mockResolvedValue(baseRepair)
    updateRepair.mockResolvedValue({
      ...baseRepair,
      end_data: '2026-11-09T10:00:00',
    })
    renderAt('/repairs/1')

    await screen.findByText('LORENZA')
    fireEvent.click(screen.getByRole('button', { name: 'Archive repair' }))
    await waitFor(() => expect(updateRepair).toHaveBeenCalled())
    expect(updateRepair.mock.calls[0][1]).toMatchObject({
      end_data: expect.any(String),
    })
  })

  it('prefills the start date for a new repair', async () => {
    getRepair.mockResolvedValue(null)
    renderAt('/repairs/new')

    const start = (await screen.findByLabelText('Start date')) as HTMLInputElement
    expect(start.value).not.toBe('')
  })

  it('uploads a picture taken from the repair page without a filename prompt', async () => {
    getRepair.mockResolvedValue(baseRepair)
    uploadPicture.mockResolvedValue({
      id: 5,
      path: 'repair/2026-11-21-0001.jpg',
      owner_type: 'repair',
      owner_id: 1,
    })
    renderAt('/repairs/1')

    await screen.findByText('LORENZA')
    const input = screen.getByTestId('picture-input') as HTMLInputElement
    expect(input.getAttribute('accept')).toBe('image/*')
    expect(input.getAttribute('capture')).toBe('environment')

    const file = new File(['bytes'], 'shot.jpg', { type: 'image/jpeg' })
    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => expect(uploadPicture).toHaveBeenCalledWith(file, 'repair', 1))
    expect(await screen.findByAltText('Picture 5')).toBeTruthy()
  })

  it('shows the repair pictures as thumbnails', async () => {
    getRepair.mockResolvedValue({
      ...baseRepair,
      pictures: [
        {
          id: 5,
          path: 'repair/2026-11-21-0001.jpg',
          owner_type: 'repair',
          owner_id: 1,
        },
      ],
    })
    renderAt('/repairs/1')

    const image = (await screen.findByAltText('Picture 5')) as HTMLImageElement
    expect(image.getAttribute('src')).toBe('/api/v1/pictures/5/file')
  })

  it('deletes a picture from the repair page', async () => {
    getRepair.mockResolvedValue({
      ...baseRepair,
      pictures: [
        { id: 5, path: 'repair/x.jpg', owner_type: 'repair', owner_id: 1 },
      ],
    })
    deletePicture.mockResolvedValue(undefined)
    renderAt('/repairs/1')

    await screen.findByAltText('Picture 5')
    fireEvent.click(screen.getByRole('button', { name: 'Delete picture 5' }))

    await waitFor(() => expect(deletePicture).toHaveBeenCalledWith(5))
    await waitFor(() => expect(screen.queryByAltText('Picture 5')).toBeNull())
  })

  it('stops a work-log entry by setting its end time', async () => {
    getRepair.mockResolvedValue({
      ...baseRepair,
      work_log: [
        {
          id: 10,
          start_time: '2026-11-01T09:00:00',
          end_time: null,
          operator: 'LORENZA',
        },
      ],
    })
    updateWorkLog.mockResolvedValue({ id: 10 })
    renderAt('/repairs/1')

    await screen.findByText('LORENZA')
    fireEvent.click(screen.getByRole('button', { name: 'Stop work log 10' }))
    await waitFor(() => expect(updateWorkLog).toHaveBeenCalled())
    expect(updateWorkLog.mock.calls[0][1]).toBe(10)
    expect(updateWorkLog.mock.calls[0][2]).toMatchObject({
      end_time: expect.any(String),
    })
  })
})
