import { api } from './client'
import type { Customer, Vehicle } from './types'

export async function listCustomers(): Promise<Customer[]> {
  const { data } = await api.GET('/api/v1/customers')
  return data ?? []
}

export async function listVehicles(): Promise<Vehicle[]> {
  const { data } = await api.GET('/api/v1/vehicles')
  return data ?? []
}

export async function getVehicle(id: number): Promise<Vehicle> {
  const { data } = await api.GET('/api/v1/vehicles/{vehicle_id}', {
    params: { path: { vehicle_id: id } },
  })
  return data as Vehicle
}
