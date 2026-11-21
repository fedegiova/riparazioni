import { api } from './client'
import type { GasCylinder, ServicePart } from './types'

export async function listServiceParts(): Promise<ServicePart[]> {
  const { data } = await api.GET('/api/v1/service-parts')
  return data ?? []
}

export async function listGasCylinders(): Promise<GasCylinder[]> {
  const { data } = await api.GET('/api/v1/gas-cylinders')
  return data ?? []
}
