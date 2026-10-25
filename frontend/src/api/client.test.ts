import { afterEach, describe, expect, it, vi } from 'vitest'
import { request } from './client'

function jsonResponse(status: number, payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('api client', () => {
  it('resolves a 2xx response to the parsed JSON body', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(200, [{ id: 1, name: 'v1' }]))
    vi.stubGlobal('fetch', fetchMock)

    const data = await request<{ id: number; name: string }[]>('GET', '/vehicles')

    expect(data).toEqual([{ id: 1, name: 'v1' }])
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/vehicles',
      expect.objectContaining({ method: 'GET' }),
    )
  })

  it('rejects with an ApiError carrying the envelope message on 4xx', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse(409, { error: 'Still referenced by a repair' }),
      ),
    )

    await expect(request('DELETE', '/refrigerators/9')).rejects.toMatchObject({
      name: 'ApiError',
      status: 409,
      message: 'Still referenced by a repair',
    })
  })

  it('rejects with a fallback message including the status when the body is not an envelope', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response('Internal Server Error', { status: 500 }),
      ),
    )

    await expect(request('GET', '/vehicles')).rejects.toMatchObject({
      name: 'ApiError',
      status: 500,
      message: expect.stringContaining('500'),
    })
  })
})
