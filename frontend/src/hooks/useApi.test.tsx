import { act, renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ApiError } from '../api/client'
import { useApi } from './useApi'

describe('useApi', () => {
  it('loads data and clears loading', async () => {
    const { result } = renderHook(() => useApi(() => Promise.resolve([1, 2]), []))

    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.data).toEqual([1, 2])
    expect(result.current.error).toBeNull()
  })

  it('exposes the ApiError message', async () => {
    const { result } = renderHook(() =>
      useApi(() => Promise.reject(new ApiError(409, 'Customer does not exist')), []),
    )

    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.error).toBe('Customer does not exist')
  })

  it('reloads data', async () => {
    let calls = 0
    const { result } = renderHook(() => useApi(() => Promise.resolve(++calls), []))

    await waitFor(() => expect(result.current.data).toBe(1))
    await act(async () => {
      await result.current.reload()
    })
    expect(result.current.data).toBe(2)
  })
})
