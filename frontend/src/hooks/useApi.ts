import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError } from '../api/client'

export type ApiState<T> = {
  data: T | null
  error: string | null
  loading: boolean
  reload: () => Promise<void>
}

/**
 * Minimal data-loading hook over the shared API client. The loader is held in
 * a ref so callers can pass an inline closure; `deps` controls re-fetching.
 * Failures exposed as the `ApiError` message (or a generic fallback).
 */
export function useApi<T>(
  loader: () => Promise<T>,
  deps: readonly unknown[] = [],
): ApiState<T> {
  const loaderRef = useRef(loader)
  loaderRef.current = loader

  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const reload = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setData(await loaderRef.current())
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unexpected error')
    } finally {
      setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => {
    void reload()
  }, [reload])

  return { data, error, loading, reload }
}
