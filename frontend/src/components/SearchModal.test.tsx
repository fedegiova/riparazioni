import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import SearchModal from './SearchModal'

afterEach(cleanup)

describe('SearchModal', () => {
  it('filters the loaded list and returns a selection', async () => {
    const load = vi
      .fn()
      .mockResolvedValue([
        { id: 1, name: 'ACME' },
        { id: 2, name: 'Beta' },
      ])
    const onSelect = vi.fn()

    render(
      <SearchModal
        open
        title="Pick a customer"
        cacheKey="search-modal-test"
        load={load}
        getKey={(item) => item.id}
        getLabel={(item) => item.name}
        onClose={() => {}}
        onSelect={onSelect}
      />,
    )

    expect(await screen.findByText('ACME')).toBeTruthy()
    expect(load).toHaveBeenCalledTimes(1)

    fireEvent.change(screen.getByLabelText('Search'), {
      target: { value: 'bet' },
    })
    expect(screen.queryByText('ACME')).toBeNull()
    expect(screen.getByText('Beta')).toBeTruthy()

    fireEvent.click(screen.getByText('Beta'))
    expect(onSelect).toHaveBeenCalledWith({ id: 2, name: 'Beta' })
  })
})
