import { useState } from 'react'
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
import PhotoLibraryIcon from '@mui/icons-material/PhotoLibrary'
import {
  createServicePart,
  deleteServicePart,
  listServiceParts,
  updateServicePart,
} from '../api/equipment'
import type { ServicePart, ServicePartInput } from '../api/types'
import { useApi } from '../hooks/useApi'
import PictureSection from './PictureSection'

type PartDraft = {
  name: string
  supplier: string
  kind: string
  price: string
  notes: string
}

const EMPTY_DRAFT: PartDraft = {
  name: '',
  supplier: '',
  kind: '',
  price: '',
  notes: '',
}

function toDraft(part: ServicePart): PartDraft {
  return {
    name: part.name ?? '',
    supplier: part.supplier ?? '',
    kind: part.kind ?? '',
    price: part.price != null ? String(part.price) : '',
    notes: part.notes ?? '',
  }
}

function toInput(draft: PartDraft, isRefrigeratorPart: boolean): ServicePartInput {
  return {
    name: draft.name || undefined,
    supplier: draft.supplier || undefined,
    kind: draft.kind || undefined,
    price: draft.price ? Number(draft.price) : undefined,
    is_refrigerator_part: isRefrigeratorPart,
    notes: draft.notes || undefined,
  }
}

type PartsManagerProps = {
  isRefrigeratorPart: boolean
}

function PartsManager({ isRefrigeratorPart }: PartsManagerProps) {
  const { data, error, loading, reload } = useApi(
    () => listServiceParts(isRefrigeratorPart),
    [isRefrigeratorPart],
  )

  const [editing, setEditing] = useState<ServicePart | null>(null)
  const [draft, setDraft] = useState<PartDraft>(EMPTY_DRAFT)
  const [formOpen, setFormOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [toDelete, setToDelete] = useState<ServicePart | null>(null)
  const [picturesOf, setPicturesOf] = useState<ServicePart | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  function openCreate() {
    setEditing(null)
    setDraft(EMPTY_DRAFT)
    setActionError(null)
    setFormOpen(true)
  }

  function openEdit(part: ServicePart) {
    setEditing(part)
    setDraft(toDraft(part))
    setActionError(null)
    setFormOpen(true)
  }

  async function handleSave() {
    setSaving(true)
    setActionError(null)
    try {
      const input = toInput(draft, isRefrigeratorPart)
      if (editing) {
        await updateServicePart(editing.id, input)
      } else {
        await createServicePart(input)
      }
      setFormOpen(false)
      await reload()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Unexpected error')
    } finally {
      setSaving(false)
    }
  }

  async function confirmDelete() {
    if (!toDelete) return
    setActionError(null)
    try {
      await deleteServicePart(toDelete.id)
      setToDelete(null)
      await reload()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Unexpected error')
      setToDelete(null)
    }
  }

  if (loading) return <CircularProgress />

  if (error) return <Alert severity="error">{error}</Alert>

  const parts = data ?? []

  return (
    <Box>
      {actionError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {actionError}
        </Alert>
      )}

      <Stack direction="row" sx={{ justifyContent: 'flex-end', mb: 2 }}>
        <Button variant="contained" onClick={openCreate}>
          New part
        </Button>
      </Stack>

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Supplier</TableCell>
              <TableCell>Kind</TableCell>
              <TableCell>Price</TableCell>
              <TableCell>Notes</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {parts.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6}>
                  <Typography color="text.secondary">No parts.</Typography>
                </TableCell>
              </TableRow>
            ) : (
              parts.map((part) => (
                <TableRow key={part.id}>
                  <TableCell>{part.name ?? '—'}</TableCell>
                  <TableCell>{part.supplier ?? '—'}</TableCell>
                  <TableCell>{part.kind ?? '—'}</TableCell>
                  <TableCell>{part.price ?? '—'}</TableCell>
                  <TableCell>{part.notes ?? '—'}</TableCell>
                  <TableCell align="right">
                    <IconButton
                      aria-label={`Pictures ${part.name ?? 'part'}`}
                      onClick={() => setPicturesOf(part)}
                    >
                      <PhotoLibraryIcon />
                    </IconButton>
                    <IconButton
                      aria-label={`Edit ${part.name ?? 'part'}`}
                      onClick={() => openEdit(part)}
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      aria-label={`Delete ${part.name ?? 'part'}`}
                      onClick={() => setToDelete(part)}
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
        <DialogTitle>{editing ? 'Edit part' : 'New part'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="Name"
              value={draft.name}
              onChange={(event) =>
                setDraft((current) => ({ ...current, name: event.target.value }))
              }
            />
            <TextField
              label="Supplier"
              value={draft.supplier}
              onChange={(event) =>
                setDraft((current) => ({ ...current, supplier: event.target.value }))
              }
            />
            <TextField
              label="Kind"
              value={draft.kind}
              onChange={(event) =>
                setDraft((current) => ({ ...current, kind: event.target.value }))
              }
            />
            <TextField
              label="Price"
              type="number"
              value={draft.price}
              onChange={(event) =>
                setDraft((current) => ({ ...current, price: event.target.value }))
              }
            />
            <TextField
              label="Notes"
              multiline
              minRows={2}
              value={draft.notes}
              onChange={(event) =>
                setDraft((current) => ({ ...current, notes: event.target.value }))
              }
            />
          </Stack>
          {editing && (
            <Box sx={{ mt: 2 }}>
              <PictureSection ownerType="spare" ownerId={editing.id} />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFormOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={picturesOf !== null} onClose={() => setPicturesOf(null)} fullWidth>
        <DialogTitle>Pictures — {picturesOf?.name ?? 'part'}</DialogTitle>
        <DialogContent>
          {picturesOf && (
            <PictureSection ownerType="spare" ownerId={picturesOf.id} />
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={toDelete !== null} onClose={() => setToDelete(null)}>
        <DialogTitle>Delete part</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Delete “{toDelete?.name ?? 'this part'}”? This cannot be undone.
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

export default PartsManager
