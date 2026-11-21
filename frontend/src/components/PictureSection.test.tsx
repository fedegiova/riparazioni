import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import PictureSection from './PictureSection'
import type { Picture } from '../api/types'

const { listPictures, uploadPicture, deletePicture } = vi.hoisted(() => ({
  listPictures: vi.fn(),
  uploadPicture: vi.fn(),
  deletePicture: vi.fn(),
}))

vi.mock('../api/pictures', () => ({
  listPictures,
  uploadPicture,
  deletePicture,
  pictureThumbnailUrl: (id: number) => `/api/v1/pictures/${id}/thumbnail`,
  pictureFileUrl: (id: number) => `/api/v1/pictures/${id}/file`,
}))

vi.mock('yet-another-react-lightbox', () => ({
  default: (props: { open?: boolean; slides?: Array<{ src: string }>; index?: number }) => {
    if (!props.open) return null
    return (
      <div data-testid="gallery">{props.slides?.[props.index ?? 0]?.src}</div>
    )
  },
}))

function picture(id: number): Picture {
  return { id, path: `repair/${id}.jpg`, owner_type: 'repair', owner_id: 1 }
}

beforeEach(() => {
  vi.clearAllMocks()
})

afterEach(() => {
  cleanup()
})

describe('PictureSection', () => {
  it('fetches pictures on demand and shows thumbnails from the minified view', async () => {
    listPictures.mockResolvedValue([picture(5)])
    render(<PictureSection ownerType="spare" ownerId={3} />)

    const image = (await screen.findByAltText('Picture 5')) as HTMLImageElement
    expect(image.getAttribute('src')).toBe('/api/v1/pictures/5/thumbnail')
    expect(listPictures).toHaveBeenCalledWith('spare', 3)
  })

  it('seeds from initialPictures without fetching', async () => {
    render(
      <PictureSection ownerType="repair" ownerId={1} initialPictures={[picture(5)]} />,
    )

    expect(await screen.findByAltText('Picture 5')).toBeTruthy()
    expect(listPictures).not.toHaveBeenCalled()
  })

  it('uploads a captured picture without a filename prompt and appends it', async () => {
    listPictures.mockResolvedValue([])
    uploadPicture.mockResolvedValue(picture(5))
    render(<PictureSection ownerType="spare" ownerId={3} />)

    const input = screen.getByTestId('picture-input') as HTMLInputElement
    expect(input.getAttribute('accept')).toBe('image/*')
    expect(input.getAttribute('capture')).toBe('environment')

    const file = new File(['bytes'], 'shot.jpg', { type: 'image/jpeg' })
    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => expect(uploadPicture).toHaveBeenCalledWith(file, 'spare', 3))
    expect(await screen.findByAltText('Picture 5')).toBeTruthy()
  })

  it('deletes a picture', async () => {
    listPictures.mockResolvedValue([picture(5)])
    deletePicture.mockResolvedValue(undefined)
    render(<PictureSection ownerType="cylinder" ownerId={7} />)

    await screen.findByAltText('Picture 5')
    fireEvent.click(screen.getByRole('button', { name: 'Delete picture 5' }))

    await waitFor(() => expect(deletePicture).toHaveBeenCalledWith(5))
    await waitFor(() => expect(screen.queryByAltText('Picture 5')).toBeNull())
  })

  it('opens the gallery on the full-size picture when a thumbnail is activated', async () => {
    listPictures.mockResolvedValue([picture(5)])
    render(<PictureSection ownerType="spare" ownerId={3} />)

    fireEvent.click(await screen.findByAltText('Picture 5'))
    expect((await screen.findByTestId('gallery')).textContent).toBe(
      '/api/v1/pictures/5/file',
    )
  })
})
