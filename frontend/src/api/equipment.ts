import { api } from './client'
import type {
  CylinderOperation,
  GasCylinder,
  GasCylinderInput,
  Refill,
  RefillInput,
  Refrigerator,
  RefrigeratorInput,
  ServicePart,
  ServicePartInput,
} from './types'

// --- Refrigerators -----------------------------------------------------------

export async function listRefrigerators(
  allestimentoId?: number,
): Promise<Refrigerator[]> {
  const { data } = await api.GET('/api/v1/refrigerators', {
    params: {
      query:
        allestimentoId === undefined
          ? {}
          : { allestimento_id: allestimentoId },
    },
  })
  return data ?? []
}

export async function createRefrigerator(
  input: RefrigeratorInput,
): Promise<Refrigerator> {
  const { data } = await api.POST('/api/v1/refrigerators', { body: input })
  return data as Refrigerator
}

export async function getRefrigerator(id: number): Promise<Refrigerator> {
  const { data } = await api.GET('/api/v1/refrigerators/{refrigerator_id}', {
    params: { path: { refrigerator_id: id } },
  })
  return data as Refrigerator
}

export async function updateRefrigerator(
  id: number,
  input: RefrigeratorInput,
): Promise<Refrigerator> {
  const { data } = await api.PUT('/api/v1/refrigerators/{refrigerator_id}', {
    params: { path: { refrigerator_id: id } },
    body: input,
  })
  return data as Refrigerator
}

export async function installRefrigerator(
  id: number,
  allestimentoId: number,
): Promise<Refrigerator> {
  const { data } = await api.POST('/api/v1/refrigerators/{refrigerator_id}/install', {
    params: { path: { refrigerator_id: id } },
    body: { allestimento_id: allestimentoId },
  })
  return data as Refrigerator
}

export async function deleteRefrigerator(id: number): Promise<void> {
  await api.DELETE('/api/v1/refrigerators/{refrigerator_id}', {
    params: { path: { refrigerator_id: id } },
  })
}

// --- Service parts -----------------------------------------------------------

export async function listServiceParts(
  isRefrigeratorPart?: boolean,
): Promise<ServicePart[]> {
  const { data } = await api.GET('/api/v1/service-parts', {
    params: {
      query:
        isRefrigeratorPart === undefined
          ? {}
          : { is_refrigerator_part: isRefrigeratorPart },
    },
  })
  return data ?? []
}

export async function createServicePart(
  input: ServicePartInput,
): Promise<ServicePart> {
  const { data } = await api.POST('/api/v1/service-parts', { body: input })
  return data as ServicePart
}

export async function updateServicePart(
  id: number,
  input: ServicePartInput,
): Promise<ServicePart> {
  const { data } = await api.PUT('/api/v1/service-parts/{part_id}', {
    params: { path: { part_id: id } },
    body: input,
  })
  return data as ServicePart
}

export async function deleteServicePart(id: number): Promise<void> {
  await api.DELETE('/api/v1/service-parts/{part_id}', {
    params: { path: { part_id: id } },
  })
}

// --- Gas cylinders -----------------------------------------------------------

export async function listGasCylinders(
  includeArchived = false,
): Promise<GasCylinder[]> {
  const { data } = await api.GET('/api/v1/gas-cylinders', {
    params: { query: includeArchived ? { archived: true } : {} },
  })
  return data ?? []
}

export async function getGasCylinder(id: number): Promise<GasCylinder> {
  const { data } = await api.GET('/api/v1/gas-cylinders/{cylinder_id}', {
    params: { path: { cylinder_id: id } },
  })
  return data as GasCylinder
}

export async function createGasCylinder(
  input: GasCylinderInput,
): Promise<GasCylinder> {
  const { data } = await api.POST('/api/v1/gas-cylinders', {
    body: input as never,
  })
  return data as GasCylinder
}

export async function updateGasCylinder(
  id: number,
  input: GasCylinderInput,
): Promise<GasCylinder> {
  const { data } = await api.PUT('/api/v1/gas-cylinders/{cylinder_id}', {
    params: { path: { cylinder_id: id } },
    body: input,
  })
  return data as GasCylinder
}

export async function deleteGasCylinder(id: number): Promise<void> {
  await api.DELETE('/api/v1/gas-cylinders/{cylinder_id}', {
    params: { path: { cylinder_id: id } },
  })
}

export async function archiveGasCylinder(id: number): Promise<GasCylinder> {
  const { data } = await api.POST('/api/v1/gas-cylinders/{cylinder_id}/archive', {
    params: { path: { cylinder_id: id } },
  })
  return data as GasCylinder
}

export async function restoreGasCylinder(id: number): Promise<GasCylinder> {
  const { data } = await api.POST('/api/v1/gas-cylinders/{cylinder_id}/restore', {
    params: { path: { cylinder_id: id } },
  })
  return data as GasCylinder
}

export async function listGasCylinderRefills(id: number): Promise<Refill[]> {
  const { data } = await api.GET('/api/v1/gas-cylinders/{cylinder_id}/refills', {
    params: { path: { cylinder_id: id } },
  })
  return data ?? []
}

export async function getCylinderOperations(
  id: number,
): Promise<CylinderOperation[]> {
  const { data } = await api.GET(
    '/api/v1/gas-cylinders/{cylinder_id}/operations',
    {
      params: { path: { cylinder_id: id } },
    },
  )
  return data ?? []
}

export async function createGasCylinderRefill(
  id: number,
  input: RefillInput = {},
): Promise<Refill> {
  const { data } = await api.POST(
    '/api/v1/gas-cylinders/{cylinder_id}/refills',
    {
      params: { path: { cylinder_id: id } },
      body: input,
    },
  )
  return data as Refill
}
