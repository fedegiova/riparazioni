import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import CylindersManager from './CylindersManager'

const {
  listGasCylinders,
  createGasCylinder,
  updateGasCylinder,
  deleteGasCylinder,
  archiveGasCylinder,
  restoreGasCylinder,
  createGasCylinderRefill,
} = vi.hoisted(() => ({
  listGasCylinders: vi.fn(),
  createGasCylinder: vi.fn(),
  updateGasCylinder: vi.fn(),
  deleteGasCylinder: vi.fn(),
  archiveGasCylinder: vi.fn(),
  restoreGasCylinder: vi.fn(),
  createGasCylinderRefill: vi.fn(),
}))

const { getGasTypes } = vi.hoisted(() => ({ getGasTypes: vi.fn() }))

vi.mock('../api/equipment', () => ({
  listGasCylinders,
  createGasCylinder,
  updateGasCylinder,
  deleteGasCylinder,
  archiveGasCylinder,
  restoreGasCylinder,
  createGasCylinderRefill,
}))

vi.mock('../api/settings', () => ({ getGasTypes }))

beforeEach(() => {
  vi.resetAllMocks()
  getGasTypes.mockResolvedValue([])
  listGasCylinders.mockResolvedValue([])
})

afterEach(() => {
  cleanup()
})

/** MUI keeps a closing dialog mounted for its exit transition (~195ms). */
async function waitForDialogToClose() {
  await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
}

describe('CylindersManager', () => {
  it('renders the state summary and each cylinder fill', async () => {
    listGasCylinders.mockResolvedValue([
      { id: 1, serial_nr: 'A', full_weight: 10, remaining_weight: 5 },
      { id: 2, serial_nr: 'B', full_weight: 10, remaining_weight: 1 },
    ])
    render(<CylindersManager />)

    expect(await screen.findByText('A')).toBeTruthy()
    expect(screen.getByText('Active: 2')).toBeTruthy()
    expect(screen.getByText('Below ¼: 1')).toBeTruthy()
    expect(screen.getByText('Archived: 0')).toBeTruthy()
    expect(screen.getByText('5 / 10 kg')).toBeTruthy()
    expect(screen.getByText('1 / 10 kg')).toBeTruthy()
  })

  it('offers the configured gas types in the editor', async () => {
    getGasTypes.mockResolvedValue(['R410A', 'R134a'])
    render(<CylindersManager />)

    await screen.findByText('No cylinders.')
    fireEvent.click(screen.getByRole('button', { name: 'New cylinder' }))

    expect(await screen.findByRole('option', { name: 'R410A' })).toBeTruthy()
    expect(screen.getByRole('option', { name: 'R134a' })).toBeTruthy()
  })

  it('creates a cylinder', async () => {
    createGasCylinder.mockResolvedValue({ id: 5 })
    render(<CylindersManager />)

    await screen.findByText('No cylinders.')
    fireEvent.click(screen.getByRole('button', { name: 'New cylinder' }))
    fireEvent.change(screen.getByLabelText('Serial number'), {
      target: { value: 'CYL-9' },
    })
    fireEvent.change(screen.getByLabelText(/Full weight/), {
      target: { value: '12' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() =>
      expect(createGasCylinder).toHaveBeenCalledWith(
        expect.objectContaining({ serial_nr: 'CYL-9', full_weight: 12 }),
      ),
    )
    await waitForDialogToClose()
  })

  it('edits a cylinder', async () => {
    listGasCylinders.mockResolvedValue([
      { id: 5, serial_nr: 'A', full_weight: 10, remaining_weight: 5 },
    ])
    updateGasCylinder.mockResolvedValue({ id: 5 })
    render(<CylindersManager />)

    await screen.findByText('A')
    fireEvent.click(screen.getByRole('button', { name: 'Edit A' }))
    fireEvent.change(screen.getByLabelText('Serial number'), {
      target: { value: 'B' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() =>
      expect(updateGasCylinder).toHaveBeenCalledWith(
        5,
        expect.objectContaining({ serial_nr: 'B' }),
      ),
    )
    await waitForDialogToClose()
  })

  it('refills a cylinder and shows the restored balance', async () => {
    listGasCylinders
      .mockResolvedValueOnce([
        { id: 1, serial_nr: 'A', full_weight: 10, remaining_weight: 1 },
      ])
      .mockResolvedValueOnce([
        { id: 1, serial_nr: 'A', full_weight: 10, remaining_weight: 10 },
      ])
    createGasCylinderRefill.mockResolvedValue({ id: 9 })
    render(<CylindersManager />)

    await screen.findByText('A')
    fireEvent.click(screen.getByRole('button', { name: 'Refill A' }))
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() =>
      expect(createGasCylinderRefill).toHaveBeenCalledWith(
        1,
        expect.objectContaining({ date: expect.any(String) }),
      ),
    )
    await waitForDialogToClose()
    expect(await screen.findByText('10 / 10 kg')).toBeTruthy()
  })

  it('archives a low cylinder and restores it', async () => {
    listGasCylinders
      .mockResolvedValueOnce([
        { id: 1, serial_nr: 'A', full_weight: 10, remaining_weight: 1 },
      ])
      .mockResolvedValueOnce([
        {
          id: 1,
          serial_nr: 'A',
          full_weight: 10,
          remaining_weight: 1,
          archived: true,
        },
      ])
    archiveGasCylinder.mockResolvedValue({ id: 1, archived: true })
    restoreGasCylinder.mockResolvedValue({ id: 1, archived: false })
    render(<CylindersManager />)

    await screen.findByText('A')
    fireEvent.click(screen.getByRole('button', { name: 'Archive A' }))
    await waitFor(() => expect(archiveGasCylinder).toHaveBeenCalledWith(1))

    fireEvent.click(await screen.findByRole('button', { name: 'Restore A' }))
    await waitFor(() => expect(restoreGasCylinder).toHaveBeenCalledWith(1))
  })

  it('reports a referenced-cylinder deletion error', async () => {
    listGasCylinders.mockResolvedValue([
      { id: 1, serial_nr: 'A', full_weight: 10, remaining_weight: 5 },
    ])
    deleteGasCylinder.mockRejectedValue(
      new Error('Cylinder is referenced by a work log'),
    )
    render(<CylindersManager />)

    await screen.findByText('A')
    fireEvent.click(screen.getByRole('button', { name: 'Delete A' }))
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }))

    expect(
      await screen.findByText('Cylinder is referenced by a work log'),
    ).toBeTruthy()
    expect(screen.getByText('A')).toBeTruthy()
  })
})
