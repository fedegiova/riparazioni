import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from './client'
import {
  deletePicture,
  listPictures,
  pictureFileUrl,
  pictureThumbnailUrl,
  uploadPicture,
} from './pictures'

vi.mock('./client', () => ({
  api: { GET: vi.fn(), POST: vi.fn(), DELETE: vi.fn() },
}))

const apiMock = api as unknown as {
  GET: ReturnType<typeof vi.fn>
  POST: ReturnType<typeof vi.fn>
  DELETE: ReturnType<typeof vi.fn>
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('uploadPicture', () => {
  it('posts multipart form data carrying the owner and no filename prompt', async () => {
    apiMock.POST.mockResolvedValue({
      data: {
        id: 7,
        path: 'repair/2026-11-21-0001.jpg',
        owner_type: 'repair',
        owner_id: 12,
      },
      response: new Response(),
    })

    const file = new File(['bytes'], 'photo.jpg', { type: 'image/jpeg' })
    const picture = await uploadPicture(file, 'repair', 12, 'fede')

    expect(picture.id).toBe(7)
    expect(apiMock.POST).toHaveBeenCalledTimes(1)
    const [path, options] = apiMock.POST.mock.calls[0]
    expect(path).toBe('/api/v1/pictures')

    const body = options.body as FormData
    expect(body).toBeInstanceOf(FormData)
    expect(body.get('file')).toBeInstanceOf(File)
    expect(body.get('owner_type')).toBe('repair')
    expect(body.get('owner_id')).toBe('12')
    expect(body.get('uploaded_by')).toBe('fede')
  })

  it('materializes the file into an in-memory blob before upload', async () => {
    apiMock.POST.mockResolvedValue({
      data: { id: 1, path: 'repair/x.jpg', owner_type: 'repair', owner_id: 1 },
      response: new Response(),
    })

    const file = new File(['hello-bytes'], 'a.jpg', { type: 'image/jpeg' })
    await uploadPicture(file, 'repair', 1)

    const body = apiMock.POST.mock.calls[0][1].body as FormData
    const sent = body.get('file') as File
    expect(await sent.text()).toBe('hello-bytes')
    expect(sent.name).toBe('a.jpg')
    expect(sent.type).toBe('image/jpeg')
  })

  it('falls back to FileReader when arrayBuffer returns no bytes', async () => {
    apiMock.POST.mockResolvedValue({
      data: { id: 1, path: 'repair/x.jpg', owner_type: 'repair', owner_id: 1 },
      response: new Response(),
    })

    const file = new File(['hello-bytes'], 'a.jpg', { type: 'image/jpeg' })
    Object.defineProperty(file, 'arrayBuffer', {
      value: vi.fn().mockResolvedValue(new ArrayBuffer(0)),
    })

    await uploadPicture(file, 'repair', 1)

    const body = apiMock.POST.mock.calls[0][1].body as FormData
    const sent = body.get('file') as File
    expect(await sent.text()).toBe('hello-bytes')
  })

  it('falls back to FileReader when arrayBuffer throws', async () => {
    apiMock.POST.mockResolvedValue({
      data: { id: 1, path: 'repair/x.jpg', owner_type: 'repair', owner_id: 1 },
      response: new Response(),
    })

    const file = new File(['hello-bytes'], 'a.jpg', { type: 'image/jpeg' })
    Object.defineProperty(file, 'arrayBuffer', {
      value: vi.fn().mockRejectedValue(new Error('cannot read')),
    })

    await uploadPicture(file, 'repair', 1)

    const body = apiMock.POST.mock.calls[0][1].body as FormData
    const sent = body.get('file') as File
    expect(await sent.text()).toBe('hello-bytes')
  })

  it('rejects when the file cannot be read at all', async () => {
    const file = new File([], 'empty.jpg', { type: 'image/jpeg' })

    await expect(uploadPicture(file, 'repair', 1)).rejects.toThrow(
      'The photo could not be read',
    )
    expect(apiMock.POST).not.toHaveBeenCalled()
  })

  it('gives the file part a fallback name when the camera file has none', async () => {
    apiMock.POST.mockResolvedValue({
      data: { id: 1, path: 'repair/x.jpg', owner_type: 'repair', owner_id: 1 },
      response: new Response(),
    })

    await uploadPicture(new File(['b'], ''), 'repair', 1)

    const body = apiMock.POST.mock.calls[0][1].body as FormData
    expect((body.get('file') as File).name).toBe('photo.jpg')
  })

  it('omits uploaded_by when not provided', async () => {
    apiMock.POST.mockResolvedValue({
      data: { id: 1, path: 'repair/x.jpg', owner_type: 'repair', owner_id: 1 },
      response: new Response(),
    })

    await uploadPicture(new File(['b'], 'a.jpg'), 'repair', 1)

    const body = apiMock.POST.mock.calls[0][1].body as FormData
    expect(body.get('uploaded_by')).toBeNull()
  })
})

describe('listPictures', () => {
  it('queries by owner', async () => {
    apiMock.GET.mockResolvedValue({ data: [], response: new Response() })

    await listPictures('cylinder', 4)

    const [path, options] = apiMock.GET.mock.calls[0]
    expect(path).toBe('/api/v1/pictures')
    expect(options.params.query).toEqual({ owner_type: 'cylinder', owner_id: 4 })
  })
})

describe('deletePicture', () => {
  it('deletes by id', async () => {
    apiMock.DELETE.mockResolvedValue({ data: undefined, response: new Response() })

    await deletePicture(7)

    const [path, options] = apiMock.DELETE.mock.calls[0]
    expect(path).toBe('/api/v1/pictures/{picture_id}')
    expect(options.params.path).toEqual({ picture_id: 7 })
  })
})

describe('pictureFileUrl', () => {
  it('builds the same-origin download URL', () => {
    expect(pictureFileUrl(7)).toBe('/api/v1/pictures/7/file')
  })
})

describe('pictureThumbnailUrl', () => {
  it('builds the same-origin minified-view URL', () => {
    expect(pictureThumbnailUrl(7)).toBe('/api/v1/pictures/7/thumbnail')
  })
})
