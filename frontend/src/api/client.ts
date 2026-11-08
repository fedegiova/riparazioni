// Shared client for the /api/v1 backend. All data access in the app goes
// through `api` below: a typed openapi-fetch client whose per-endpoint
// signatures and request/response types are generated from
// `docs/openapi.yaml` into `src/api/generated/schema.d.ts`
// (regenerate with `npm run generate:api`).
import createFetchClient from 'openapi-fetch'

export type { components, paths } from './generated/schema'
import type { paths } from './generated/schema'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/**
 * Typed client for the /api/v1 API. No baseUrl: the OpenAPI document's paths
 * already carry the /api/v1 prefix, so every call is a same-origin relative
 * URL (served by the Vite dev proxy or by any same-origin production setup).
 *
 * 2xx responses resolve to `{ data, response }`, where `data` is the parsed
 * JSON body (typed to the document's response schema; `undefined` for 204s
 * and empty bodies). 4xx/5xx responses reject with an ApiError carrying the
 * backend error envelope message (`{"error": "message"}`), or a generic
 * message with the status when the body is not an envelope. Network failures
 * (e.g. backend down) reject with the underlying fetch error.
 */
export const api = createFetchClient<paths>()

api.use({
  async onResponse({ response }) {
    if (response.ok) return

    let message = `Request failed with status ${response.status}`
    try {
      const payload: unknown = JSON.parse(await response.text())
      if (
        typeof payload === 'object' &&
        payload !== null &&
        typeof (payload as { error?: unknown }).error === 'string' &&
        (payload as { error: string }).error !== ''
      ) {
        message = (payload as { error: string }).error
      }
    } catch {
      // Non-JSON error body: keep the generic message.
    }

    throw new ApiError(response.status, message)
  },
})
