// Shared client for the /api/v1 backend. All data access in the app goes
// through `request`; later per-endpoint helpers (src/api/*.ts) build on it.

const API_BASE = '/api/v1'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/**
 * Call a /api/v1 endpoint with a JSON body and return the parsed JSON
 * response. Non-2xx responses reject with an ApiError carrying the backend
 * error envelope message (`{"error": "message"}`), or a generic message
 * with the status when the body is not an envelope.
 */
export async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (response.ok) {
    if (response.status === 204) {
      return undefined as T
    }
    return (await response.json()) as T
  }

  let message = `Request failed with status ${response.status}`
  try {
    const payload = (await response.json()) as { error?: unknown }
    if (payload && typeof payload.error === 'string' && payload.error !== '') {
      message = payload.error
    }
  } catch {
    // Non-JSON error body: keep the generic message.
  }

  throw new ApiError(response.status, message)
}
