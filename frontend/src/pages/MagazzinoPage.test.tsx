import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import MagazzinoPage from './MagazzinoPage'

const {
  listServiceParts,
  createServicePart,
  updateServicePart,
  deleteServicePart,
  listGasCylinders,
  createGasCylinder,
  updateGasCylinder,
  deleteGasCylinder,
  archiveGasCylinder,
  restoreGasCylinder,
  createGasCylinderRefill,
} = vi.hoisted(() => ({
  listServiceParts: vi.fn(),
  createServicePart: vi.fn(),
  updateServicePart: vi.fn(),
  deleteServicePart: vi.fn(),
  listGasCylinders: vi.fn(),
  createGasCylinder: vi.fn(),
  updateGasCylinder: vi.fn(),
  deleteGasCylinder: vi.fn(),
  archiveGasCylinder: vi.fn(),
  restoreGasCylinder: vi.fn(),
  createGasCylinderRefill: vi.fn(),
}))

vi.mock('../api/equipment', () => ({
  listServiceParts,
  createServicePart,
  updateServicePart,
  deleteServicePart,
  listGasCylinders,
  createGasCylinder,
  updateGasCylinder,
  deleteGasCylinder,
  archiveGasCylinder,
  restoreGasCylinder,
  createGasCylinderRefill,
}))

vi.mock('../api/settings', () => ({
  getGasTypes: vi.fn().mockResolvedValue([]),
}))

vi.mock('../api/pictures', () => ({
  listPictures: vi.fn().mockResolvedValue([]),
  uploadPicture: vi.fn(),
  deletePicture: vi.fn(),
  pictureThumbnailUrl: (id: number) => `/api/v1/pictures/${id}/thumbnail`,
  pictureFileUrl: (id: number) => `/api/v1/pictures/${id}/file`,
}))

vi.mock('yet-another-react-lightbox', () => ({
  default: () => null,
}))

const regularPart = { id: 1, name: 'Compressor', supplier: 'ACME', kind: 'fridge' }
const fridgePart = { id: 2, name: 'Thermostat', supplier: 'Cool', kind: 'fridge' }

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

/** MUI keeps a closing dialog mounted for its exit transition (~195ms). */
async function waitForDialogToClose() {
  await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
}

function renderPage() {
  return render(
    <MemoryRouter>
      <MagazzinoPage />
    </MemoryRouter>,
  )
}

describe('MagazzinoPage', () => {
  it('renders the three tabs with Ricambi selected by default', async () => {
    listServiceParts.mockResolvedValue([regularPart])
    renderPage()

    expect(screen.getByRole('tab', { name: 'Ricambi' })).toBeTruthy()
    expect(screen.getByRole('tab', { name: 'Ricambi Frigo' })).toBeTruthy()
    expect(screen.getByRole('tab', { name: 'Bombole' })).toBeTruthy()
    expect(
      screen.getByRole('tab', { name: 'Ricambi' }).getAttribute('aria-selected'),
    ).toBe('true')
    expect(await screen.findByText('Compressor')).toBeTruthy()
  })

  it('shows the cylinder overview on the Bombole tab', async () => {
    listServiceParts.mockResolvedValue([])
    listGasCylinders.mockResolvedValue([
      {
        id: 1,
        serial_nr: 'CYL-1',
        gas_kind: 'R410A',
        full_weight: 10,
        remaining_weight: 2.5,
      },
    ])
    renderPage()

    fireEvent.click(screen.getByRole('tab', { name: 'Bombole' }))

    expect(await screen.findByText('CYL-1')).toBeTruthy()
    expect(screen.getByText('Active: 1')).toBeTruthy()
    expect(screen.getByText('2.5 / 10 kg')).toBeTruthy()
  })

  it('manages regular parts against the API', async () => {
    listServiceParts.mockResolvedValue([regularPart])
    createServicePart.mockResolvedValue({ id: 3 })
    updateServicePart.mockResolvedValue({ id: 1 })
    deleteServicePart.mockResolvedValue(undefined)
    renderPage()
    await screen.findByText('Compressor')

    fireEvent.click(screen.getByRole('button', { name: 'New part' }))
    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Fan' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    await waitFor(() =>
      expect(createServicePart).toHaveBeenCalledWith(
        expect.objectContaining({ name: 'Fan', is_refrigerator_part: false }),
      ),
    )
    await waitForDialogToClose()
    await screen.findByText('Compressor')

    fireEvent.click(screen.getByRole('button', { name: 'Edit Compressor' }))
    fireEvent.change(screen.getByLabelText('Name'), {
      target: { value: 'Compressor XL' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    await waitFor(() =>
      expect(updateServicePart).toHaveBeenCalledWith(
        1,
        expect.objectContaining({
          name: 'Compressor XL',
          is_refrigerator_part: false,
        }),
      ),
    )
    await waitForDialogToClose()
    await screen.findByText('Compressor')

    fireEvent.click(screen.getByRole('button', { name: 'Delete Compressor' }))
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }))
    await waitFor(() => expect(deleteServicePart).toHaveBeenCalledWith(1))
  })

  it('manages refrigerator parts against the API', async () => {
    listServiceParts.mockResolvedValue([fridgePart])
    createServicePart.mockResolvedValue({ id: 4 })
    updateServicePart.mockResolvedValue({ id: 2 })
    deleteServicePart.mockResolvedValue(undefined)
    renderPage()
    fireEvent.click(screen.getByRole('tab', { name: 'Ricambi Frigo' }))
    await screen.findByText('Thermostat')

    fireEvent.click(screen.getByRole('button', { name: 'New part' }))
    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Sensor' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    await waitFor(() =>
      expect(createServicePart).toHaveBeenCalledWith(
        expect.objectContaining({ name: 'Sensor', is_refrigerator_part: true }),
      ),
    )
    await waitForDialogToClose()
    await screen.findByText('Thermostat')

    fireEvent.click(screen.getByRole('button', { name: 'Edit Thermostat' }))
    fireEvent.change(screen.getByLabelText('Name'), {
      target: { value: 'Thermostat v2' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    await waitFor(() =>
      expect(updateServicePart).toHaveBeenCalledWith(
        2,
        expect.objectContaining({
          name: 'Thermostat v2',
          is_refrigerator_part: true,
        }),
      ),
    )
    await waitForDialogToClose()
    await screen.findByText('Thermostat')

    fireEvent.click(screen.getByRole('button', { name: 'Delete Thermostat' }))
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }))
    await waitFor(() => expect(deleteServicePart).toHaveBeenCalledWith(2))
  })
})
