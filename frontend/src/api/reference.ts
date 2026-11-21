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
