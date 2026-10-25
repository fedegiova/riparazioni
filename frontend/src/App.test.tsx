import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import App from './App'

beforeEach(() => {
  window.history.pushState({}, '', '/')
})

afterEach(() => {
  cleanup()
  window.history.pushState({}, '', '/')
})

describe('app shell', () => {
  it('renders the branded shell with the home page at /', () => {
    render(<App />)

    expect(screen.getByRole('banner').textContent).toContain('Riparazioni')
    expect(screen.getByRole('main').textContent).toContain(
      'Repair management — application shell in place.',
    )
  })

  it('renders the not-found placeholder on an unmatched route', () => {
    window.history.pushState({}, '', '/definitely-not-a-route')
    render(<App />)

    // The shell stays visible on unmatched routes...
    expect(screen.getByRole('banner').textContent).toContain('Riparazioni')
    // ...and the content area shows the not-found placeholder.
    expect(screen.getByRole('main').textContent).toContain('Page not found.')
    expect(screen.getByRole('main').textContent).toContain('404')
  })
})
