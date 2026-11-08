import { describe, expect, expectTypeOf, it, vi } from 'vitest'
import type { MethodResponse } from 'openapi-fetch'
import { api, type components } from './client'

type FetchMock = ReturnType<typeof vi.fn>

function jsonResponse(status: number, payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

// The client captures globalThis.fetch at creation time, so the mock is
// passed per request via openapi-fetch's `fetch` option.
function mockFetch(resolving: Response | Promise<Response>): FetchMock {
  return vi.fn(async (_input: Request): Promise<Response> => resolving)
}

describe('api client (generated from docs/openapi.yaml)', () => {
  it('resolves a 2xx response to the parsed JSON body on the right URL', async () => {
    const payload = [{ id: 1, targa: 'AB123CD' }]
    const fetchMock = mockFetch(jsonResponse(200, payload))

    const { data } = await api.GET('/api/v1/vehicles', {
      fetch: fetchMock as unknown as typeof fetch,
    })

    expect(data).toEqual(payload)
    const request = fetchMock.mock.calls[0][0] as Request
    expect(request.url).toContain('/api/v1/vehicles')
    expect(request.method).toBe('GET')
  })

  it('rejects with an ApiError carrying the envelope message on 4xx', async () => {
    const fetchMock = mockFetch(
      jsonResponse(409, { error: 'Still referenced by a repair' }),
    )

    const promise = api.DELETE('/api/v1/refrigerators/{refrigerator_id}', {
      params: { path: { refrigerator_id: 9 } },
      fetch: fetchMock as unknown as typeof fetch,
    })
    await expect(promise).rejects.toMatchObject({
      name: 'ApiError',
      status: 409,
      message: 'Still referenced by a repair',
    })

    const request = fetchMock.mock.calls[0][0] as Request
    expect(request.url).toContain('/api/v1/refrigerators/9')
    expect(request.method).toBe('DELETE')
  })

  it('rejects with a fallback message including the status when the body is not an envelope', async () => {
    const fetchMock = mockFetch(new Response('Internal Server Error', { status: 500 }))

    await expect(
      api.GET('/api/v1/vehicles', { fetch: fetchMock as unknown as typeof fetch }),
    ).rejects.toMatchObject({
      name: 'ApiError',
      status: 500,
      message: expect.stringContaining('500'),
    })
  })

  it('resolves a 204 response to undefined data', async () => {
    const fetchMock = mockFetch(new Response(null, { status: 204 }))

    const { data } = await api.DELETE('/api/v1/refrigerators/{refrigerator_id}', {
      params: { path: { refrigerator_id: 9 } },
      fetch: fetchMock as unknown as typeof fetch,
    })

    expect(data).toBeUndefined()
  })

  it('types the vehicles list data to the document schema', () => {
    // The call signature comes from the generated paths type: the data for
    // GET /api/v1/vehicles is exactly the document's Vehicle[] shape.
    type VehicleList = MethodResponse<typeof api, 'get', '/api/v1/vehicles'>
    expectTypeOf<VehicleList>().toEqualTypeOf<components['schemas']['Vehicle'][]>()
  })

  it('sends the picture upload as a multipart form', async () => {
    const fetchMock = mockFetch(
      jsonResponse(201, { id: 7, path: 'pictures/ab12cd.jpg' }),
    )

    const form = new FormData()
    form.append('file', new Blob(['image-bytes']), 'image.jpg')
    form.append('uploaded_by', 'fede')

    const { data } = await api.POST('/api/v1/pictures', {
      // openapi-typescript models the multipart body as the document's
      // { file, uploaded_by } object; the runtime body is a real FormData,
      // which openapi-fetch passes through to fetch unserialized.
      body: form as unknown as { file: string; uploaded_by?: string },
      fetch: fetchMock as unknown as typeof fetch,
    })

    expect(data).toMatchObject({ id: 7, path: 'pictures/ab12cd.jpg' })
    const request = fetchMock.mock.calls[0][0] as Request
    expect(request.url).toContain('/api/v1/pictures')
    expect(request.method).toBe('POST')
    expect(request.headers.get('content-type')).toMatch(/^multipart\/form-data/)
  })
})
