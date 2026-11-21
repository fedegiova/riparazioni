import { useEffect, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  IconButton,
  LinearProgress,
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
import DeleteIcon from '@mui/icons-material/Delete'
import EditIcon from '@mui/icons-material/Edit'
import HistoryIcon from '@mui/icons-material/History'
import { useNavigate } from 'react-router-dom'
import {
  archiveGasCylinder,
  createGasCylinder,
  createGasCylinderRefill,
  deleteGasCylinder,
  listGasCylinders,
  restoreGasCylinder,
  updateGasCylinder,
} from '../api/equipment'
import { getGasTypes } from '../api/settings'
import type { GasCylinder, GasCylinderInput } from '../api/types'
import { useApi } from '../hooks/useApi'

type CylinderDraft = {
  gas_kind: string
  serial_nr: string
  model: string
  full_weight: string
  remaining_weight: string
  notes: string
}

const EMPTY_DRAFT: CylinderDraft = {
  gas_kind: '',
  serial_nr: '',
  model: '',
  full_weight: '',
  remaining_weight: '',
  notes: '',
}

function toDraft(cylinder: GasCylinder): CylinderDraft {
  return {
    gas_kind: cylinder.gas_kind ?? '',
    serial_nr: cylinder.serial_nr ?? '',
    model: cylinder.model ?? '',
    full_weight: cylinder.full_weight != null ? String(cylinder.full_weight) : '',
    remaining_weight:
      cylinder.remaining_weight != null ? String(cylinder.remaining_weight) : '',
    notes: cylinder.notes ?? '',
  }
}

function toInput(draft: CylinderDraft, includeBalance = false): GasCylinderInput {
  return {
    gas_kind: draft.gas_kind || undefined,
    serial_nr: draft.serial_nr || undefined,
    model: draft.model || undefined,
    full_weight: draft.full_weight ? Number(draft.full_weight) : undefined,
    // The balance is seeded at creation only; the update path rejects it.
    ...(includeBalance
      ? {
          remaining_weight: draft.remaining_weight
            ? Number(draft.remaining_weight)
            : undefined,
        }
      : {}),
    notes: draft.notes || undefined,
  }
}

function label(cylinder: GasCylinder): string {
  return cylinder.serial_nr || `#${cylinder.id}`
}

/** A cylinder is "low" when its remaining weight is below a quarter of full. */
function isLow(cylinder: GasCylinder): boolean {
  const full = cylinder.full_weight
  if (!full || full <= 0) return false
  const remaining = cylinder.remaining_weight ?? full
  return remaining < full / 4
}

function formatWeight(value: number | null | undefined): string {
  if (value == null) return '—'
  return String(Number(value.toFixed(2)))
}

function fillPercent(cylinder: GasCylinder): number {
  if (!cylinder.full_weight || cylinder.full_weight <= 0) return 0
  const remaining = cylinder.remaining_weight ?? cylinder.full_weight
  return Math.max(0, Math.min(100, (remaining / cylinder.full_weight) * 100))
}

function todayIso(): string {
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${now.getFullYear()}-${month}-${day}`
}

function CylindersManager() {
  const navigate = useNavigate()
  const [showArchived, setShowArchived] = useState(false)
  const { data, error, loading, reload } = useApi(
    () => listGasCylinders(showArchived),
    [showArchived],
  )

  const [gasTypes, setGasTypes] = useState<string[]>([])

  useEffect(() => {
    let active = true
    getGasTypes()
      .then((types) => {
        if (active) setGasTypes(types)
      })
      .catch(() => {
        // The picker falls back to a free-text field when settings are down.
      })
    return () => {
      active = false
    }
  }, [])

  const [editing, setEditing] = useState<GasCylinder | null>(null)
  const [draft, setDraft] = useState<CylinderDraft>(EMPTY_DRAFT)
  const [formOpen, setFormOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [toDelete, setToDelete] = useState<GasCylinder | null>(null)
  const [toRefill, setToRefill] = useState<GasCylinder | null>(null)
  const [refillDate, setRefillDate] = useState(todayIso())
  const [refillReference, setRefillReference] = useState('')
  const [actionError, setActionError] = useState<string | null>(null)

  function openCreate() {
    setEditing(null)
    setDraft(EMPTY_DRAFT)
    setActionError(null)
    setFormOpen(true)
  }

  function openEdit(cylinder: GasCylinder) {
    setEditing(cylinder)
    setDraft(toDraft(cylinder))
    setActionError(null)
    setFormOpen(true)
  }

  function openRefill(cylinder: GasCylinder) {
    setToRefill(cylinder)
    setRefillDate(todayIso())
    setRefillReference('')
    setActionError(null)
  }

  async function handleSave() {
    setSaving(true)
    setActionError(null)
    try {
      if (draft.full_weight.trim() === '' || Number.isNaN(Number(draft.full_weight))) {
        throw new Error('Full weight is required')
      }
      if (editing === null && draft.remaining_weight.trim() !== '') {
        if (Number(draft.remaining_weight) > Number(draft.full_weight)) {
          throw new Error('Remaining weight cannot exceed the full weight')
        }
      }
      const input = toInput(draft)
      if (editing) {
        await updateGasCylinder(editing.id, input)
      } else {
        await createGasCylinder(toInput(draft, true))
      }
      setFormOpen(false)
      await reload()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Unexpected error')
    } finally {
      setSaving(false)
    }
  }

  async function handleRefill() {
    if (!toRefill) return
    setActionError(null)
    try {
      await createGasCylinderRefill(toRefill.id, {
        date: refillDate || undefined,
        reference: refillReference || undefined,
      })
      setToRefill(null)
      await reload()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Unexpected error')
      setToRefill(null)
    }
  }

  async function handleArchive(cylinder: GasCylinder) {
    setActionError(null)
    try {
      await archiveGasCylinder(cylinder.id)
      await reload()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Unexpected error')
    }
  }

  async function handleRestore(cylinder: GasCylinder) {
    setActionError(null)
    try {
      await restoreGasCylinder(cylinder.id)
      await reload()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Unexpected error')
    }
  }

  async function confirmDelete() {
    if (!toDelete) return
    setActionError(null)
    try {
      await deleteGasCylinder(toDelete.id)
      setToDelete(null)
      await reload()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Unexpected error')
      setToDelete(null)
    }
  }

  if (loading) return <CircularProgress />

  if (error) return <Alert severity="error">{error}</Alert>

  const cylinders = data ?? []
  const active = cylinders.filter((cylinder) => !cylinder.archived).length
  const archived = cylinders.filter((cylinder) => cylinder.archived).length
  const low = cylinders.filter(
    (cylinder) => !cylinder.archived && isLow(cylinder),
  ).length

  return (
    <Box>
      {actionError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {actionError}
        </Alert>
      )}

      <Stack
        direction="row"
        spacing={3}
        sx={{ mb: 2, alignItems: 'center', flexWrap: 'wrap' }}
      >
        <Typography variant="body2">Active: {active}</Typography>
        <Typography variant="body2">Below ¼: {low}</Typography>
        <Typography variant="body2">Archived: {archived}</Typography>
        <Box sx={{ flexGrow: 1 }} />
        <Button size="small" onClick={() => setShowArchived((value) => !value)}>
          {showArchived ? 'Hide archived' : 'Show archived'}
        </Button>
        <Button variant="contained" onClick={openCreate}>
          New cylinder
        </Button>
      </Stack>

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Serial</TableCell>
              <TableCell>Gas</TableCell>
              <TableCell>Model</TableCell>
              <TableCell>Fill</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {cylinders.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5}>
                  <Typography color="text.secondary">No cylinders.</Typography>
                </TableCell>
              </TableRow>
            ) : (
              cylinders.map((cylinder) => (
                <TableRow key={cylinder.id}>
                  <TableCell>{cylinder.serial_nr ?? '—'}</TableCell>
                  <TableCell>{cylinder.gas_kind ?? '—'}</TableCell>
                  <TableCell>{cylinder.model ?? '—'}</TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {formatWeight(cylinder.remaining_weight)} /{' '}
                      {formatWeight(cylinder.full_weight)} kg
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={fillPercent(cylinder)}
                      sx={{ mt: 0.5, minWidth: 120 }}
                    />
                  </TableCell>
                  <TableCell align="right">
                    <IconButton
                      aria-label={`Log ${label(cylinder)}`}
                      onClick={() => navigate(`/magazzino/bombole/${cylinder.id}`)}
                    >
                      <HistoryIcon />
                    </IconButton>
                    <IconButton
                      aria-label={`Edit ${label(cylinder)}`}
                      onClick={() => openEdit(cylinder)}
                    >
                      <EditIcon />
                    </IconButton>
                    <Button
                      size="small"
                      aria-label={`Refill ${label(cylinder)}`}
                      onClick={() => openRefill(cylinder)}
                    >
                      Refill
                    </Button>
                    {cylinder.archived ? (
                      <Button
                        size="small"
                        aria-label={`Restore ${label(cylinder)}`}
                        onClick={() => handleRestore(cylinder)}
                      >
                        Restore
                      </Button>
                    ) : (
                      <Button
                        size="small"
                        aria-label={`Archive ${label(cylinder)}`}
                        disabled={!isLow(cylinder)}
                        onClick={() => handleArchive(cylinder)}
                      >
                        Archive
                      </Button>
                    )}
                    <IconButton
                      aria-label={`Delete ${label(cylinder)}`}
                      onClick={() => setToDelete(cylinder)}
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

      <Dialog open={formOpen} onClose={() => setFormOpen(false)} fullWidth>
        <DialogTitle>{editing ? 'Edit cylinder' : 'New cylinder'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {gasTypes.length > 0 ? (
              <TextField
                select
                label="Gas type"
                value={draft.gas_kind}
                onChange={(event) =>
                  setDraft((current) => ({
                    ...current,
                    gas_kind: event.target.value,
                  }))
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
            ) : (
              <TextField
                label="Gas type"
                value={draft.gas_kind}
                onChange={(event) =>
                  setDraft((current) => ({
                    ...current,
                    gas_kind: event.target.value,
                  }))
                }
              />
            )}
            <TextField
              label="Serial number"
              value={draft.serial_nr}
              onChange={(event) =>
                setDraft((current) => ({
                  ...current,
                  serial_nr: event.target.value,
                }))
              }
            />
            <TextField
              label="Model"
              value={draft.model}
              onChange={(event) =>
                setDraft((current) => ({
                  ...current,
                  model: event.target.value,
                }))
              }
            />
            <TextField
              label="Full weight"
              type="number"
              required
              value={draft.full_weight}
              onChange={(event) =>
                setDraft((current) => ({
                  ...current,
                  full_weight: event.target.value,
                }))
              }
            />
            <TextField
              label="Remaining weight"
              type="number"
              value={draft.remaining_weight}
              disabled={editing !== null}
              helperText={
                editing
                  ? 'The balance changes only through refills and gas movements'
                  : 'Defaults to the full weight'
              }
              onChange={(event) =>
                setDraft((current) => ({
                  ...current,
                  remaining_weight: event.target.value,
                }))
              }
            />
            <TextField
              label="Notes"
              multiline
              minRows={2}
              value={draft.notes}
              onChange={(event) =>
                setDraft((current) => ({
                  ...current,
                  notes: event.target.value,
                }))
              }
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFormOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={toRefill !== null} onClose={() => setToRefill(null)} fullWidth>
        <DialogTitle>Refill cylinder</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            Refilling {toRefill ? label(toRefill) : 'this cylinder'} resets its
            remaining weight to full and restores it if archived.
          </DialogContentText>
          <Stack spacing={2}>
            <TextField
              label="Date"
              type="date"
              value={refillDate}
              onChange={(event) => setRefillDate(event.target.value)}
              slotProps={{ inputLabel: { shrink: true } }}
            />
            <TextField
              label="Reference"
              value={refillReference}
              onChange={(event) => setRefillReference(event.target.value)}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setToRefill(null)}>Cancel</Button>
          <Button variant="contained" onClick={handleRefill}>
            Save
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={toDelete !== null} onClose={() => setToDelete(null)}>
        <DialogTitle>Delete cylinder</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Delete “{toDelete ? label(toDelete) : 'this cylinder'}”? This cannot
            be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setToDelete(null)}>Cancel</Button>
          <Button color="error" onClick={confirmDelete}>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default CylindersManager
