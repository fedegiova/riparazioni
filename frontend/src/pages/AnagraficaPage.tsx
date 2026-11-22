import { useEffect, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Paper,
  Stack,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  TextField,
  Typography,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import EditIcon from '@mui/icons-material/Edit'
import SwapHorizIcon from '@mui/icons-material/SwapHoriz'
import {
  createRefrigerator,
  installRefrigerator,
  listRefrigerators,
  updateRefrigerator,
} from '../api/equipment'
import { listCustomers, listVehicles } from '../api/reference'
import { getGasTypes } from '../api/settings'
import type { Refrigerator, RefrigeratorInput } from '../api/types'
import { useApi } from '../hooks/useApi'

/** Case-insensitive "contains" match over a row's visible field values. */
function matchesQuery(
  values: Array<string | number | null | undefined>,
  query: string,
): boolean {
  const needle = query.trim().toLowerCase()
  if (!needle) return true
  return values.some((value) =>
    String(value ?? '')
      .toLowerCase()
      .includes(needle),
  )
}

/** Render a legacy value, keeping blank cells aligned with an em dash. */
function cell(value: string | number | null | undefined) {
  return value === null || value === undefined || value === '' ? '—' : value
}

function SearchBox({
  value,
  onChange,
}: {
  value: string
  onChange: (value: string) => void
}) {
  return (
    <TextField
      label="Search"
      size="small"
      fullWidth
      value={value}
      onChange={(event) => onChange(event.target.value)}
      sx={{ mb: 2, maxWidth: 320 }}
    />
  )
}

function CustomersList() {
  const { data, error, loading } = useApi(() => listCustomers(), [])
  const [query, setQuery] = useState('')

  const customers = data ?? []
  const rows = customers.filter((customer) =>
    matchesQuery(
      [
        customer.cliente,
        customer.via,
        customer.cap,
        customer.citta,
        customer.prov,
        customer.tel,
        customer.cell,
        customer.email,
      ],
      query,
    ),
  )

  return (
    <Box>
      <SearchBox value={query} onChange={setQuery} />
      {loading ? (
        <CircularProgress />
      ) : error ? (
        <Alert severity="error">{error}</Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Cliente</TableCell>
                <TableCell>Via</TableCell>
                <TableCell>CAP</TableCell>
                <TableCell>Città</TableCell>
                <TableCell>Prov</TableCell>
                <TableCell>Tel</TableCell>
                <TableCell>Cell</TableCell>
                <TableCell>Email</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8}>
                    <Typography color="text.secondary">
                      {customers.length === 0 ? 'No customers.' : 'No matches.'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                rows.map((customer) => (
                  <TableRow key={customer.id}>
                    <TableCell>{cell(customer.cliente)}</TableCell>
                    <TableCell>{cell(customer.via)}</TableCell>
                    <TableCell>{cell(customer.cap)}</TableCell>
                    <TableCell>{cell(customer.citta)}</TableCell>
                    <TableCell>{cell(customer.prov)}</TableCell>
                    <TableCell>{cell(customer.tel)}</TableCell>
                    <TableCell>{cell(customer.cell)}</TableCell>
                    <TableCell>{cell(customer.email)}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  )
}

type RefrigeratorDraft = {
  serial_nr: string
  brand: string
  model: string
  gas_kind: string
  gas_kg: string
  notes: string
}

const EMPTY_DRAFT: RefrigeratorDraft = {
  serial_nr: '',
  brand: '',
  model: '',
  gas_kind: '',
  gas_kg: '',
  notes: '',
}

function draftFrom(refrigerator: Refrigerator): RefrigeratorDraft {
  return {
    serial_nr: refrigerator.serial_nr ?? '',
    brand: refrigerator.brand ?? '',
    model: refrigerator.model ?? '',
    gas_kind: refrigerator.gas_kind ?? '',
    gas_kg: refrigerator.gas_kg != null ? String(refrigerator.gas_kg) : '',
    notes: refrigerator.notes ?? '',
  }
}

function draftToInput(draft: RefrigeratorDraft): RefrigeratorInput {
  return {
    serial_nr: draft.serial_nr.trim(),
    brand: draft.brand.trim(),
    model: draft.model.trim(),
    gas_kind: draft.gas_kind,
    gas_kg: draft.gas_kg ? Number(draft.gas_kg) : undefined,
    notes: draft.notes || undefined,
  }
}

function refrigeratorLabel(refrigerator: Refrigerator): string {
  const serial = refrigerator.serial_nr || `#${refrigerator.id}`
  return refrigerator.gas_kg != null
    ? `${serial} (${refrigerator.gas_kg} kg)`
    : serial
}

function VehiclesList() {
  const { data, error, loading, reload } = useApi(
    () =>
      Promise.all([listVehicles(), listRefrigerators()]).then(
        ([vehicles, refrigerators]) => ({ vehicles, refrigerators }),
      ),
    [],
  )
  const [query, setQuery] = useState('')
  const [gasTypes, setGasTypes] = useState<string[]>([])
  const [actionError, setActionError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  // The refrigerator dialog: adding to a free allestimento, editing the
  // installed one, or explicitly replacing it.
  const [dialog, setDialog] = useState<{
    mode: 'add' | 'edit' | 'replace'
    allestimentoId: number
    installed: Refrigerator | null
    draft: RefrigeratorDraft
  } | null>(null)

  useEffect(() => {
    let active = true
    getGasTypes()
      .then((types) => {
        if (active) setGasTypes(types)
      })
      .catch(() => {
        // Fall back to a free-text gas type when settings are unavailable.
      })
    return () => {
      active = false
    }
  }, [])

  const vehicles = data?.vehicles ?? []
  const installed = new Map<number, Refrigerator>()
  for (const refrigerator of data?.refrigerators ?? []) {
    if (refrigerator.allestimento_id != null) {
      installed.set(refrigerator.allestimento_id, refrigerator)
    }
  }

  const rows = vehicles.filter((vehicle) =>
    matchesQuery(
      [
        vehicle.targa,
        vehicle.autocarro,
        vehicle.carrozzeria,
        vehicle.modello,
        vehicle.classe,
        vehicle.commessa,
        installed.get(vehicle.id)?.serial_nr,
      ],
      query,
    ),
  )

  function openAdd(allestimentoId: number) {
    setActionError(null)
    setDialog({ mode: 'add', allestimentoId, installed: null, draft: EMPTY_DRAFT })
  }

  function openEdit(allestimentoId: number, refrigerator: Refrigerator) {
    setActionError(null)
    setDialog({
      mode: 'edit',
      allestimentoId,
      installed: refrigerator,
      draft: draftFrom(refrigerator),
    })
  }

  function openReplace(allestimentoId: number, refrigerator: Refrigerator) {
    setActionError(null)
    setDialog({
      mode: 'replace',
      allestimentoId,
      installed: refrigerator,
      draft: EMPTY_DRAFT,
    })
  }

  async function handleSave() {
    if (!dialog) return
    const input = draftToInput(dialog.draft)
    if (!input.serial_nr || !input.brand || !input.model) {
      setActionError('Serial number, manufacturer, and model are required.')
      return
    }
    if (!input.gas_kg || input.gas_kg <= 0) {
      setActionError('The nameplate capacity must be a positive number.')
      return
    }
    if (!input.gas_kind) {
      setActionError('Select a gas type.')
      return
    }
    setSaving(true)
    setActionError(null)
    try {
      if (dialog.mode === 'edit' && dialog.installed) {
        await updateRefrigerator(dialog.installed.id, input)
      } else if (dialog.mode === 'add') {
        await createRefrigerator({ ...input, allestimento_id: dialog.allestimentoId })
      } else {
        // Replace: create the new unit uninstalled, then install it (the
        // explicit replacement detaches the old one).
        const created = await createRefrigerator(input)
        await installRefrigerator(created.id, dialog.allestimentoId)
      }
      setDialog(null)
      await reload()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Unexpected error')
    } finally {
      setSaving(false)
    }
  }

  const dialogTitle =
    dialog?.mode === 'edit'
      ? 'Edit refrigerator'
      : dialog?.mode === 'replace'
        ? 'Replace refrigerator'
        : 'Add refrigerator'

  return (
    <Box>
      <SearchBox value={query} onChange={setQuery} />
      {actionError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {actionError}
        </Alert>
      )}
      {loading ? (
        <CircularProgress />
      ) : error ? (
        <Alert severity="error">{error}</Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Targa</TableCell>
                <TableCell>Autocarro</TableCell>
                <TableCell>Carrozzeria</TableCell>
                <TableCell>Modello</TableCell>
                <TableCell>Classe</TableCell>
                <TableCell>Commessa</TableCell>
                <TableCell>Refrigeratore</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8}>
                    <Typography color="text.secondary">
                      {vehicles.length === 0 ? 'No allestimenti.' : 'No matches.'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                rows.map((vehicle) => {
                  const refrigerator = installed.get(vehicle.id)
                  return (
                    <TableRow key={vehicle.id}>
                      <TableCell>{cell(vehicle.targa)}</TableCell>
                      <TableCell>{cell(vehicle.autocarro)}</TableCell>
                      <TableCell>{cell(vehicle.carrozzeria)}</TableCell>
                      <TableCell>{cell(vehicle.modello)}</TableCell>
                      <TableCell>{cell(vehicle.classe)}</TableCell>
                      <TableCell>{cell(vehicle.commessa)}</TableCell>
                      <TableCell>
                        {refrigerator ? (
                          <Typography variant="body2">
                            {refrigeratorLabel(refrigerator)}
                            <br />
                            <Typography component="span" variant="caption">
                              {refrigerator.gas_kind ?? 'no gas type'}
                            </Typography>
                          </Typography>
                        ) : (
                          'None installed'
                        )}
                      </TableCell>
                      <TableCell align="right">
                        {refrigerator ? (
                          <>
                            <IconButton
                              aria-label={`Edit refrigerator for ${vehicle.targa ?? vehicle.id}`}
                              onClick={() => openEdit(vehicle.id, refrigerator)}
                            >
                              <EditIcon />
                            </IconButton>
                            <IconButton
                              aria-label={`Replace refrigerator for ${vehicle.targa ?? vehicle.id}`}
                              onClick={() => openReplace(vehicle.id, refrigerator)}
                            >
                              <SwapHorizIcon />
                            </IconButton>
                          </>
                        ) : (
                          <Button
                            size="small"
                            startIcon={<AddIcon />}
                            aria-label={`Add refrigerator for ${vehicle.targa ?? vehicle.id}`}
                            onClick={() => openAdd(vehicle.id)}
                          >
                            Add refrigerator
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  )
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={dialog !== null} onClose={() => setDialog(null)} fullWidth>
        <DialogTitle>{dialogTitle}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="Serial number"
              value={dialog?.draft.serial_nr ?? ''}
              onChange={(event) =>
                setDialog((current) =>
                  current
                    ? { ...current, draft: { ...current.draft, serial_nr: event.target.value } }
                    : current,
                )
              }
            />
            <TextField
              label="Manufacturer"
              value={dialog?.draft.brand ?? ''}
              onChange={(event) =>
                setDialog((current) =>
                  current
                    ? { ...current, draft: { ...current.draft, brand: event.target.value } }
                    : current,
                )
              }
            />
            <TextField
              label="Model"
              value={dialog?.draft.model ?? ''}
              onChange={(event) =>
                setDialog((current) =>
                  current
                    ? { ...current, draft: { ...current.draft, model: event.target.value } }
                    : current,
                )
              }
            />
            <TextField
              select
              label="Gas type"
              value={dialog?.draft.gas_kind ?? ''}
              onChange={(event) =>
                setDialog((current) =>
                  current
                    ? { ...current, draft: { ...current.draft, gas_kind: event.target.value } }
                    : current,
                )
              }
              slotProps={{ select: { native: true } }}
            >
              <option value="">—</option>
              {gasTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </TextField>
            <TextField
              label="Nameplate capacity (kg)"
              type="number"
              required
              value={dialog?.draft.gas_kg ?? ''}
              onChange={(event) =>
                setDialog((current) =>
                  current
                    ? { ...current, draft: { ...current.draft, gas_kg: event.target.value } }
                    : current,
                )
              }
            />
            <TextField
              label="Notes"
              multiline
              minRows={2}
              value={dialog?.draft.notes ?? ''}
              onChange={(event) =>
                setDialog((current) =>
                  current
                    ? { ...current, draft: { ...current.draft, notes: event.target.value } }
                    : current,
                )
              }
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialog(null)}>Cancel</Button>
          <Button variant="contained" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

function AnagraficaPage() {
  const [tab, setTab] = useState(0)

  return (
    <Box>
      <Typography variant="h4" component="h1" sx={{ mb: 2 }}>
        Anagrafica
      </Typography>
      <Tabs
        value={tab}
        onChange={(_, value: number) => setTab(value)}
        aria-label="Anagrafica sections"
      >
        <Tab label="Clienti" />
        <Tab label="Allestimenti" />
      </Tabs>
      <Box sx={{ mt: 2 }}>
        {tab === 0 && <CustomersList />}
        {tab === 1 && <VehiclesList />}
      </Box>
    </Box>
  )
}

export default AnagraficaPage
