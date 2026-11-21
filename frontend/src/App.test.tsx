import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'

const { listRepairs } = vi.hoisted(() => ({ listRepairs: vi.fn() }))

vi.mock('./api/repairs', () => ({
  listRepairs,
  getRepair: vi.fn(),
  createRepair: vi.fn(),
  updateRepair: vi.fn(),
  deleteRepair: vi.fn(),
  addWorkLog: vi.fn(),
  updateWorkLog: vi.fn(),
  deleteWorkLog: vi.fn(),
  repairsExportUrl: vi.fn(),
}))

beforeEach(() => {
  listRepairs.mockResolvedValue([])
  window.history.pushState({}, '', '/')
})

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
  window.history.pushState({}, '', '/')
})

describe('app shell', () => {
  it('renders the branded shell with the active-repairs landing at /', async () => {
    render(<App />)

    expect(screen.getByRole('banner').textContent).toContain('Riparazioni')
    expect(await screen.findByRole('heading', { name: 'Active repairs' })).toBeTruthy()
    expect(screen.getByLabelText('Breadcrumb').textContent).toContain('Home')
  })

  it('switches sections with the bottom navigation', async () => {
    render(<App />)

    fireEvent.click(screen.getByRole('button', { name: 'Magazzino' }))
    expect(await screen.findByRole('heading', { name: 'Magazzino' })).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: 'Anagrafica' }))
    expect(await screen.findByRole('heading', { name: 'Anagrafica' })).toBeTruthy()
  })

  it('returns to the landing with the app-bar home control', async () => {
    window.history.pushState({}, '', '/repairs')
    render(<App />)

    expect(await screen.findByRole('heading', { name: 'Repairs' })).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Go to home' }))
    expect(await screen.findByRole('heading', { name: 'Active repairs' })).toBeTruthy()
  })

  it('renders the not-found placeholder on an unmatched route', () => {
    window.history.pushState({}, '', '/definitely-not-a-route')
    render(<App />)

    expect(screen.getByRole('banner').textContent).toContain('Riparazioni')
    expect(screen.getByRole('main').textContent).toContain('Page not found.')
    expect(screen.getByRole('main').textContent).toContain('404')
  })
})
