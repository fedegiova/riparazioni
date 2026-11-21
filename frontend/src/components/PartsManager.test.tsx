import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import PartsManager from './PartsManager'
import type { Picture } from '../api/types'

const {
  listServiceParts,
  createServicePart,
  updateServicePart,
  deleteServicePart,
  listPictures,
  uploadPicture,
  deletePicture,
} = vi.hoisted(() => ({
  listServiceParts: vi.fn(),
  createServicePart: vi.fn(),
  updateServicePart: vi.fn(),
  deleteServicePart: vi.fn(),
  listPictures: vi.fn(),
  uploadPicture: vi.fn(),
  deletePicture: vi.fn(),
}))

vi.mock('../api/equipment', () => ({
  listServiceParts,
  createServicePart,
  updateServicePart,
  deleteServicePart,
}))

vi.mock('../api/pictures', () => ({
  listPictures,
  uploadPicture,
  deletePicture,
  pictureThumbnailUrl: (id: number) => `/api/v1/pictures/${id}/thumbnail`,
  pictureFileUrl: (id: number) => `/api/v1/pictures/${id}/file`,
}))

vi.mock('yet-another-react-lightbox', () => ({
  default: () => null,
}))

const part = { id: 1, name: 'Compressor', supplier: 'ACME', kind: 'fridge' }

function picture(id: number): Picture {
  return { id, path: `spare/${id}.jpg`, owner_type: 'spare', owner_id: 1 }
}

beforeEach(() => {
  vi.clearAllMocks()
  listServiceParts.mockResolvedValue([part])
  listPictures.mockResolvedValue([])
})

afterEach(() => {
  cleanup()
})

describe('PartsManager pictures', () => {
  it("opens a part's Pictures dialog and loads that part's pictures", async () => {
    listPictures.mockResolvedValue([picture(5)])
    render(<PartsManager isRefrigeratorPart={false} />)
    await screen.findByText('Compressor')

    fireEvent.click(screen.getByRole('button', { name: 'Pictures Compressor' }))

    expect(await screen.findByAltText('Picture 5')).toBeTruthy()
    expect(listPictures).toHaveBeenCalledWith('spare', 1)
  })

  it('uploads a captured picture for a spare part', async () => {
    uploadPicture.mockResolvedValue(picture(5))
    render(<PartsManager isRefrigeratorPart={false} />)
    await screen.findByText('Compressor')

    fireEvent.click(screen.getByRole('button', { name: 'Pictures Compressor' }))
    const input = await screen.findByTestId('picture-input')
    const file = new File(['bytes'], 'shot.jpg', { type: 'image/jpeg' })
    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => expect(uploadPicture).toHaveBeenCalledWith(file, 'spare', 1))
    expect(await screen.findByAltText('Picture 5')).toBeTruthy()
  })

  it("deletes a picture from a part's Pictures dialog", async () => {
    listPictures.mockResolvedValue([picture(5)])
    deletePicture.mockResolvedValue(undefined)
    render(<PartsManager isRefrigeratorPart={false} />)
    await screen.findByText('Compressor')

    fireEvent.click(screen.getByRole('button', { name: 'Pictures Compressor' }))
    await screen.findByAltText('Picture 5')
    fireEvent.click(screen.getByRole('button', { name: 'Delete picture 5' }))

    await waitFor(() => expect(deletePicture).toHaveBeenCalledWith(5))
    await waitFor(() => expect(screen.queryByAltText('Picture 5')).toBeNull())
  })

  it('shows pictures inside the edit dialog for an existing part', async () => {
    render(<PartsManager isRefrigeratorPart={false} />)
    await screen.findByText('Compressor')

    fireEvent.click(screen.getByRole('button', { name: 'Edit Compressor' }))

    expect(await screen.findByRole('button', { name: 'Add picture' })).toBeTruthy()
    expect(listPictures).toHaveBeenCalledWith('spare', 1)
  })

  it('offers no picture controls while creating a new part', async () => {
    render(<PartsManager isRefrigeratorPart={false} />)
    await screen.findByText('Compressor')

    fireEvent.click(screen.getByRole('button', { name: 'New part' }))

    expect(screen.queryByRole('button', { name: 'Add picture' })).toBeNull()
    expect(listPictures).not.toHaveBeenCalled()
  })
})
