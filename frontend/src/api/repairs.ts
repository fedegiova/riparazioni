// Data access for repairs and work-log entries. All calls go through the
// shared generated client; `ApiError` is thrown by the client middleware for
// non-2xx responses.
import { api } from './client'
import type {
  Repair,
  RepairCreate,
  RepairDetail,
  RepairUpdate,
  WorkLogCreate,
  WorkLogEntry,
  WorkLogInput,
} from './types'

export type RepairFilters = {
  customer?: number
  vehicle?: number
  refrigerator?: number
  start_date_from?: string
  start_date_to?: string
}

export async function listRepairs(filters: RepairFilters = {}): Promise<Repair[]> {
  const { data } = await api.GET('/api/v1/repairs', {
    params: { query: filters },
  })
  return data ?? []
}

export async function getRepair(id: number): Promise<RepairDetail> {
  const { data } = await api.GET('/api/v1/repairs/{repair_id}', {
    params: { path: { repair_id: id } },
  })
  return data as RepairDetail
}

export async function createRepair(body: RepairCreate): Promise<RepairDetail> {
  const { data } = await api.POST('/api/v1/repairs', { body })
  return data as RepairDetail
}

export async function updateRepair(
  id: number,
  body: RepairUpdate,
): Promise<RepairDetail> {
  const { data } = await api.PUT('/api/v1/repairs/{repair_id}', {
    params: { path: { repair_id: id } },
    body,
  })
  return data as RepairDetail
}

export async function deleteRepair(id: number): Promise<void> {
  await api.DELETE('/api/v1/repairs/{repair_id}', {
    params: { path: { repair_id: id } },
  })
}

export async function addWorkLog(
  repairId: number,
  body: WorkLogCreate,
): Promise<WorkLogEntry> {
  const { data } = await api.POST('/api/v1/repairs/{repair_id}/work-log', {
    params: { path: { repair_id: repairId } },
    body,
  })
  return data as WorkLogEntry
}

export async function updateWorkLog(
  repairId: number,
  entryId: number,
  body: WorkLogInput,
): Promise<WorkLogEntry> {
  const { data } = await api.PUT(
    '/api/v1/repairs/{repair_id}/work-log/{entry_id}',
    {
      params: { path: { repair_id: repairId, entry_id: entryId } },
      body,
    },
  )
  return data as WorkLogEntry
}

export async function deleteWorkLog(
  repairId: number,
  entryId: number,
): Promise<void> {
  await api.DELETE('/api/v1/repairs/{repair_id}/work-log/{entry_id}', {
    params: { path: { repair_id: repairId, entry_id: entryId } },
  })
}

/** Same-origin URL that downloads the filtered repairs workbook. */
export function repairsExportUrl(filters: RepairFilters = {}): string {
  const params = new URLSearchParams()
  if (filters.customer !== undefined) params.set('customer', String(filters.customer))
  if (filters.vehicle !== undefined) params.set('vehicle', String(filters.vehicle))
  if (filters.refrigerator !== undefined) {
    params.set('refrigerator', String(filters.refrigerator))
  }
  if (filters.start_date_from) params.set('start_date_from', filters.start_date_from)
  if (filters.start_date_to) params.set('start_date_to', filters.start_date_to)

  const query = params.toString()
  return `/api/v1/repairs/export${query ? `?${query}` : ''}`
}
