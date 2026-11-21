import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'

const { listRepairs, listSettings } = vi.hoisted(() => ({
  listRepairs: vi.fn(),
  listSettings: vi.fn(),
}))

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

vi.mock('./api/settings', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./api/settings')>()
  return { ...actual, listSettings }
})

beforeEach(() => {
  listRepairs.mockResolvedValue([])
  listSettings.mockResolvedValue({
    operators: [],
    working_hours: {},
    holidays: {},
  })
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

  it('opens the settings page from the app-bar control', async () => {
    render(<App />)

    await screen.findByRole('heading', { name: 'Active repairs' })
    fireEvent.click(screen.getByRole('button', { name: 'Settings' }))
    expect(await screen.findByRole('heading', { name: 'Settings' })).toBeTruthy()
  })

  it('renders the settings route directly inside the shell', async () => {
    window.history.pushState({}, '', '/settings')
    render(<App />)

    expect(screen.getByRole('banner').textContent).toContain('Riparazioni')
    expect(await screen.findByRole('heading', { name: 'Settings' })).toBeTruthy()
    expect(screen.getByLabelText('Breadcrumb').textContent).toContain('Settings')
  })

  it('renders the not-found placeholder on an unmatched route', () => {
    window.history.pushState({}, '', '/definitely-not-a-route')
    render(<App />)

    expect(screen.getByRole('banner').textContent).toContain('Riparazioni')
    expect(screen.getByRole('main').textContent).toContain('Page not found.')
    expect(screen.getByRole('main').textContent).toContain('404')
  })
})
