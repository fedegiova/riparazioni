import { beforeEach, describe, expect, it, vi } from 'vitest'

const { api } = vi.hoisted(() => ({
  api: {
    GET: vi.fn(),
    POST: vi.fn(),
    PUT: vi.fn(),
    DELETE: vi.fn(),
  },
}))

vi.mock('./client', () => ({ api }))

import {
  archiveGasCylinder,
  createGasCylinder,
  createGasCylinderRefill,
  createServicePart,
  deleteGasCylinder,
  deleteServicePart,
  getCylinderOperations,
  getGasCylinder,
  listGasCylinderRefills,
  listGasCylinders,
  listServiceParts,
  restoreGasCylinder,
  updateGasCylinder,
  updateServicePart,
} from './equipment'

beforeEach(() => {
  vi.clearAllMocks()
})

describe('service part API wrappers', () => {
  it('lists every part when no flag is given', async () => {
    api.GET.mockResolvedValue({ data: [{ id: 1 }] })

    await expect(listServiceParts()).resolves.toEqual([{ id: 1 }])
    expect(api.GET).toHaveBeenCalledWith('/api/v1/service-parts', {
      params: { query: {} },
    })
  })

  it('filters the list by the refrigerator-part flag', async () => {
    api.GET.mockResolvedValue({ data: [] })

    await listServiceParts(true)
    expect(api.GET).toHaveBeenCalledWith('/api/v1/service-parts', {
      params: { query: { is_refrigerator_part: true } },
    })
  })

  it('creates a part', async () => {
    api.POST.mockResolvedValue({ data: { id: 3, name: 'Fan' } })
    const input = { name: 'Fan', is_refrigerator_part: false }

    await expect(createServicePart(input)).resolves.toEqual({ id: 3, name: 'Fan' })
    expect(api.POST).toHaveBeenCalledWith('/api/v1/service-parts', { body: input })
  })

  it('updates a part by id', async () => {
    api.PUT.mockResolvedValue({ data: { id: 1 } })
    const input = { name: 'Compressor XL', is_refrigerator_part: false }

    await updateServicePart(1, input)
    expect(api.PUT).toHaveBeenCalledWith('/api/v1/service-parts/{part_id}', {
      params: { path: { part_id: 1 } },
      body: input,
    })
  })

  it('deletes a part by id', async () => {
    api.DELETE.mockResolvedValue({ data: undefined })

    await deleteServicePart(1)
    expect(api.DELETE).toHaveBeenCalledWith('/api/v1/service-parts/{part_id}', {
      params: { path: { part_id: 1 } },
    })
  })
})

describe('gas cylinder API wrappers', () => {
  it('lists active cylinders by default', async () => {
    api.GET.mockResolvedValue({ data: [{ id: 1 }] })

    await expect(listGasCylinders()).resolves.toEqual([{ id: 1 }])
    expect(api.GET).toHaveBeenCalledWith('/api/v1/gas-cylinders', {
      params: { query: {} },
    })
  })

  it('includes archived cylinders when requested', async () => {
    api.GET.mockResolvedValue({ data: [] })

    await listGasCylinders(true)
    expect(api.GET).toHaveBeenCalledWith('/api/v1/gas-cylinders', {
      params: { query: { archived: true } },
    })
  })

  it('creates a cylinder', async () => {
    api.POST.mockResolvedValue({ data: { id: 7 } })
    const input = { gas_kind: 'R410A', full_weight: 10 }

    await expect(createGasCylinder(input)).resolves.toEqual({ id: 7 })
    expect(api.POST).toHaveBeenCalledWith('/api/v1/gas-cylinders', {
      body: input,
    })
  })

  it('updates a cylinder by id', async () => {
    api.PUT.mockResolvedValue({ data: { id: 7 } })
    const input = { full_weight: 12 }

    await updateGasCylinder(7, input)
    expect(api.PUT).toHaveBeenCalledWith('/api/v1/gas-cylinders/{cylinder_id}', {
      params: { path: { cylinder_id: 7 } },
      body: input,
    })
  })

  it('deletes a cylinder by id', async () => {
    api.DELETE.mockResolvedValue({ data: undefined })

    await deleteGasCylinder(7)
    expect(api.DELETE).toHaveBeenCalledWith('/api/v1/gas-cylinders/{cylinder_id}', {
      params: { path: { cylinder_id: 7 } },
    })
  })

  it('archives a cylinder', async () => {
    api.POST.mockResolvedValue({ data: { id: 7, archived: true } })

    await expect(archiveGasCylinder(7)).resolves.toEqual({ id: 7, archived: true })
    expect(api.POST).toHaveBeenCalledWith(
      '/api/v1/gas-cylinders/{cylinder_id}/archive',
      { params: { path: { cylinder_id: 7 } } },
    )
  })

  it('restores a cylinder', async () => {
    api.POST.mockResolvedValue({ data: { id: 7, archived: false } })

    await expect(restoreGasCylinder(7)).resolves.toEqual({
      id: 7,
      archived: false,
    })
    expect(api.POST).toHaveBeenCalledWith(
      '/api/v1/gas-cylinders/{cylinder_id}/restore',
      { params: { path: { cylinder_id: 7 } } },
    )
  })

  it('lists the refills of a cylinder', async () => {
    api.GET.mockResolvedValue({ data: [{ id: 1 }] })

    await expect(listGasCylinderRefills(7)).resolves.toEqual([{ id: 1 }])
    expect(api.GET).toHaveBeenCalledWith(
      '/api/v1/gas-cylinders/{cylinder_id}/refills',
      { params: { path: { cylinder_id: 7 } } },
    )
  })

  it('records a refill for a cylinder', async () => {
    api.POST.mockResolvedValue({ data: { id: 2 } })
    const input = { date: '2026-11-21', reference: 'Supplier A' }

    await expect(createGasCylinderRefill(7, input)).resolves.toEqual({ id: 2 })
    expect(api.POST).toHaveBeenCalledWith(
      '/api/v1/gas-cylinders/{cylinder_id}/refills',
      {
        params: { path: { cylinder_id: 7 } },
        body: input,
      },
    )
  })

  it('defaults a refill to an empty body', async () => {
    api.POST.mockResolvedValue({ data: { id: 3 } })

    await createGasCylinderRefill(7)
    expect(api.POST).toHaveBeenCalledWith(
      '/api/v1/gas-cylinders/{cylinder_id}/refills',
      {
        params: { path: { cylinder_id: 7 } },
        body: {},
      },
    )
  })

  it('lists the operations of a cylinder', async () => {
    api.GET.mockResolvedValue({ data: [{ kind: 'refill' }] })

    await expect(getCylinderOperations(7)).resolves.toEqual([{ kind: 'refill' }])
    expect(api.GET).toHaveBeenCalledWith(
      '/api/v1/gas-cylinders/{cylinder_id}/operations',
      { params: { path: { cylinder_id: 7 } } },
    )
  })

  it('gets a single cylinder by id', async () => {
    api.GET.mockResolvedValue({ data: { id: 7, full_weight: 10 } })

    await expect(getGasCylinder(7)).resolves.toEqual({ id: 7, full_weight: 10 })
    expect(api.GET).toHaveBeenCalledWith('/api/v1/gas-cylinders/{cylinder_id}', {
      params: { path: { cylinder_id: 7 } },
    })
  })
})
