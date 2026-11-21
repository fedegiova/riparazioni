import { useEffect, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  IconButton,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import ArchiveIcon from '@mui/icons-material/Archive'
import DeleteIcon from '@mui/icons-material/Delete'
import EditIcon from '@mui/icons-material/Edit'
import SearchIcon from '@mui/icons-material/Search'
import StopCircleIcon from '@mui/icons-material/StopCircle'
import { useNavigate, useParams } from 'react-router-dom'
import { listServiceParts } from '../api/equipment'
import { listCustomers, listVehicles } from '../api/reference'
import {
  createRepair,
  deleteWorkLog,
  getRepair,
  updateRepair,
  updateWorkLog,
} from '../api/repairs'
import type { ServicePart } from '../api/types'
import SearchModal from '../components/SearchModal'
import { useApi } from '../hooks/useApi'
import {
  formatDateTime,
  nowDateTimeInput,
  toDateInput,
  toDateTimeInput,
  toIso,
} from '../lib/format'

type PartRow = {
  id_part: number
  name: string
  quantity: number
  unit_price: number | null
}

function RepairPage() {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const isNew = id === undefined
  const repairId = id ? Number(id) : null

  const {
    data: repair,
    error: loadError,
    loading: loadingRepair,
    reload,
  } = useApi(
    () => (repairId === null ? Promise.resolve(null) : getRepair(repairId)),
    [repairId],
  )

  const [customer, setCustomer] = useState<{ id: number; name: string } | null>(null)
  const [vehicle, setVehicle] = useState<{ id: number; label: string } | null>(null)
  const [startDate, setStartDate] = useState(nowDateTimeInput)
  const [deliveryDate, setDeliveryDate] = useState('')
  const [notes, setNotes] = useState('')
  const [parts, setParts] = useState<PartRow[]>([])

  const [customerModal, setCustomerModal] = useState(false)
  const [vehicleModal, setVehicleModal] = useState(false)
  const [partModal, setPartModal] = useState(false)

  const [saving, setSaving] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  useEffect(() => {
    if (!repair) return
    setCustomer(
      repair.customer != null
        ? { id: repair.customer, name: repair.customer_name ?? `#${repair.customer}` }
        : null,
    )
    setVehicle(
      repair.vehicle != null ? { id: repair.vehicle, label: `#${repair.vehicle}` } : null,
    )
    setStartDate(toDateTimeInput(repair.start_data))
    setDeliveryDate(toDateInput(repair.delivery_date))
    setNotes(repair.notes ?? '')
    setParts(
      (repair.parts ?? []).map((part) => ({
        id_part: part.id_part,
        name: part.part?.name ?? `Part #${part.id_part}`,
        quantity: part.quantity,
        unit_price: part.unit_price ?? part.part?.price ?? null,
      })),
    )
  }, [repair])

  async function handleSave() {
    setSaving(true)
    setActionError(null)
    try {
      const body = {
        customer: customer?.id,
        vehicle: vehicle?.id,
        start_data: toIso(startDate),
        delivery_date: deliveryDate || null,
        notes: notes || undefined,
        parts: parts.map((part) => ({
          id_part: part.id_part,
          quantity: part.quantity,
          unit_price: part.unit_price,
        })),
      }
      if (isNew) {
        const created = await createRepair(body)
        navigate(`/repairs/${created.id}`)
      } else if (repairId !== null) {
        await updateRepair(repairId, body)
        await reload()
      }
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Unexpected error')
    } finally {
      setSaving(false)
    }
  }

  async function handleArchive() {
    if (repairId === null) return
    setActionError(null)
    try {
      await updateRepair(repairId, { end_data: new Date().toISOString() })
      await reload()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Unexpected error')
    }
  }

  async function handleCancelEntry(entryId: number) {
    if (repairId === null) return
    setActionError(null)
    try {
      await deleteWorkLog(repairId, entryId)
      await reload()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Unexpected error')
    }
  }

  async function handleStopEntry(entryId: number) {
    if (repairId === null) return
    setActionError(null)
    try {
      await updateWorkLog(repairId, entryId, {
        end_time: new Date().toISOString(),
      })
      await reload()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Unexpected error')
    }
  }

  function updateQuantity(idPart: number, value: string) {
    const quantity = Number(value)
    setParts((current) =>
      current.map((part) =>
        part.id_part === idPart
          ? { ...part, quantity: Number.isFinite(quantity) ? quantity : 1 }
          : part,
      ),
    )
  }

  function removePart(idPart: number) {
    setParts((current) => current.filter((part) => part.id_part !== idPart))
  }

  if (loadingRepair) return <CircularProgress />

  if (loadError) return <Alert severity="error">{loadError}</Alert>

  const workLog = repair?.work_log ?? []

  return (
    <Box>
      <Typography variant="h4" component="h1" sx={{ mb: 2 }}>
        {isNew ? 'New repair' : `Repair #${repairId}`}
      </Typography>

      {actionError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {actionError}
        </Alert>
      )}

      <Paper sx={{ p: 2, mb: 2 }}>
        <Stack spacing={2}>
          <Stack
            direction={{ xs: 'column', sm: 'row' }}
            spacing={1}
            sx={{ alignItems: { sm: 'center' } }}
          >
            <TextField
              label="Cliente"
              value={customer?.name ?? ''}
              fullWidth
              slotProps={{ htmlInput: { readOnly: true } }}
            />
            <Button startIcon={<SearchIcon />} onClick={() => setCustomerModal(true)}>
              Search
            </Button>
          </Stack>
          <Stack
            direction={{ xs: 'column', sm: 'row' }}
            spacing={1}
            sx={{ alignItems: { sm: 'center' } }}
          >
            <TextField
              label="Targa"
              value={vehicle?.label ?? ''}
              fullWidth
              slotProps={{ htmlInput: { readOnly: true } }}
            />
            <Button startIcon={<SearchIcon />} onClick={() => setVehicleModal(true)}>
              Search
            </Button>
          </Stack>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField
              label="Start date"
              type="datetime-local"
              value={startDate}
              onChange={(event) => setStartDate(event.target.value)}
              fullWidth
              slotProps={{ inputLabel: { shrink: true } }}
            />
            <TextField
              label="Delivery date"
              type="date"
              value={deliveryDate}
              onChange={(event) => setDeliveryDate(event.target.value)}
              fullWidth
              slotProps={{ inputLabel: { shrink: true } }}
            />
          </Stack>
          <TextField
            label="Notes"
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            multiline
            minRows={2}
            fullWidth
          />
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button onClick={() => navigate(-1)}>Cancel</Button>
            <Button variant="contained" onClick={handleSave} disabled={saving}>
              {saving ? 'Saving…' : 'Save'}
            </Button>
          </Box>
        </Stack>
      </Paper>

      {!isNew && (
        <>
          <Paper sx={{ p: 2, mb: 2 }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                mb: 1,
              }}
            >
              <Typography variant="h6">Parts</Typography>
              <Button startIcon={<AddIcon />} onClick={() => setPartModal(true)}>
                Add part
              </Button>
            </Box>
            <TableContainer>
              <Table aria-label="Parts">
                <TableHead>
                  <TableRow>
                    <TableCell>Part</TableCell>
                    <TableCell>Quantity</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {parts.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={3}>No parts.</TableCell>
                    </TableRow>
                  ) : (
                    parts.map((part) => (
                      <TableRow key={part.id_part}>
                        <TableCell>{part.name}</TableCell>
                        <TableCell>
                          <TextField
                            type="number"
                            value={part.quantity}
                            onChange={(event) =>
                              updateQuantity(part.id_part, event.target.value)
                            }
                            slotProps={{ htmlInput: { min: 1 } }}
                            aria-label={`Quantity for ${part.name}`}
                          />
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            color="error"
                            aria-label={`Delete part ${part.name}`}
                            onClick={() => removePart(part.id_part)}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>

          <Paper sx={{ p: 2, mb: 2 }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                mb: 1,
              }}
            >
              <Typography variant="h6">Work log</Typography>
              <Button
                startIcon={<AddIcon />}
                onClick={() => navigate(`/repairs/${repairId}/work-log/new`)}
              >
                Add work log
              </Button>
            </Box>
            <TableContainer>
              <Table aria-label="Work log">
                <TableHead>
                  <TableRow>
                    <TableCell>Start</TableCell>
                    <TableCell>End</TableCell>
                    <TableCell>Operator</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {workLog.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4}>No work-log entries.</TableCell>
                    </TableRow>
                  ) : (
                    workLog.map((entry) => (
                      <TableRow key={entry.id}>
                        <TableCell>{formatDateTime(entry.start_time)}</TableCell>
                        <TableCell>{formatDateTime(entry.end_time)}</TableCell>
                        <TableCell>{entry.operator ?? '—'}</TableCell>
                        <TableCell align="right">
                          <IconButton
                            aria-label={`Stop work log ${entry.id}`}
                            disabled={Boolean(entry.end_time)}
                            onClick={() => handleStopEntry(entry.id)}
                          >
                            <StopCircleIcon />
                          </IconButton>
                          <IconButton
                            aria-label={`Edit work log ${entry.id}`}
                            onClick={() =>
                              navigate(`/repairs/${repairId}/work-log/${entry.id}`)
                            }
                          >
                            <EditIcon />
                          </IconButton>
                          <IconButton
                            color="error"
                            aria-label={`Cancel work log ${entry.id}`}
                            onClick={() => handleCancelEntry(entry.id)}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>

          <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              color="success"
              startIcon={<ArchiveIcon />}
              onClick={handleArchive}
              disabled={Boolean(repair?.end_data)}
            >
              {repair?.end_data ? 'Archived' : 'Archive repair'}
            </Button>
          </Box>
        </>
      )}

      <SearchModal
        open={customerModal}
        title="Select customer"
        cacheKey="customers"
        load={listCustomers}
        getKey={(item) => item.id}
        getLabel={(item) => item.cliente ?? `Customer #${item.id}`}
        getSecondary={(item) => item.citta ?? undefined}
        onClose={() => setCustomerModal(false)}
        onSelect={(item) => {
          setCustomer({
            id: item.id,
            name: item.cliente ?? `Customer #${item.id}`,
          })
          setCustomerModal(false)
        }}
      />

      <SearchModal
        open={vehicleModal}
        title="Select vehicle"
        cacheKey="vehicles"
        load={listVehicles}
        getKey={(item) => item.id}
        getLabel={(item) => item.targa ?? `Vehicle #${item.id}`}
        getSecondary={(item) => item.modello ?? undefined}
        onClose={() => setVehicleModal(false)}
        onSelect={(item) => {
          setVehicle({ id: item.id, label: item.targa ?? `#${item.id}` })
          setVehicleModal(false)
        }}
      />

      <SearchModal<ServicePart>
        open={partModal}
        title="Add part"
        cacheKey="service-parts"
        load={listServiceParts}
        getKey={(item) => item.id}
        getLabel={(item) => item.name ?? `Part #${item.id}`}
        getSecondary={(item) => item.kind ?? undefined}
        onClose={() => setPartModal(false)}
        onSelect={(item) => {
          setParts((current) => [
            ...current,
            {
              id_part: item.id,
              name: item.name ?? `Part #${item.id}`,
              quantity: 1,
              unit_price: item.price ?? null,
            },
          ])
          setPartModal(false)
        }}
      />
    </Box>
  )
}

export default RepairPage
