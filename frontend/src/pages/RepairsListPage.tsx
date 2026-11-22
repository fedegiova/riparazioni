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
import ChevronRightIcon from '@mui/icons-material/ChevronRight'
import DeleteIcon from '@mui/icons-material/Delete'
import DownloadIcon from '@mui/icons-material/Download'
import { useNavigate } from 'react-router-dom'
import {
  deleteRepair,
  listRepairs,
  repairsExportUrl,
  type RepairFilters,
} from '../api/repairs'
import type { Repair } from '../api/types'
import { useApi } from '../hooks/useApi'
import { downloadUrl } from '../lib/download'
import { formatDate, formatHours } from '../lib/format'

type DraftFilters = {
  customer: string
  vehicle: string
  startFrom: string
  startTo: string
}

const EMPTY_FILTERS: DraftFilters = {
  customer: '',
  vehicle: '',
  startFrom: '',
  startTo: '',
}

function toFilters(draft: DraftFilters): RepairFilters {
  return {
    customer: draft.customer ? Number(draft.customer) : undefined,
    vehicle: draft.vehicle ? Number(draft.vehicle) : undefined,
    start_date_from: draft.startFrom || undefined,
    start_date_to: draft.startTo || undefined,
  }
}

function RepairsListPage() {
  const navigate = useNavigate()
  const [draft, setDraft] = useState<DraftFilters>(EMPTY_FILTERS)
  const [applied, setApplied] = useState<DraftFilters>(EMPTY_FILTERS)
  const filters = toFilters(applied)

  const { data, error, loading, reload } = useApi(() => listRepairs(filters), [
    applied.customer,
    applied.vehicle,
    applied.startFrom,
    applied.startTo,
  ])

  const [toDelete, setToDelete] = useState<Repair | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  async function confirmDelete() {
    if (!toDelete) return
    setActionError(null)
    try {
      await deleteRepair(toDelete.id)
      setToDelete(null)
      await reload()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Unexpected error')
    }
  }

  function applyFilters() {
    setApplied(draft)
  }

  function clearFilters() {
    setDraft(EMPTY_FILTERS)
    setApplied(EMPTY_FILTERS)
  }

  function updateDraft(field: keyof DraftFilters, value: string) {
    setDraft((current) => ({ ...current, [field]: value }))
  }

  return (
    <Box>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          mb: 2,
          gap: 2,
        }}
      >
        <Typography variant="h4" component="h1">
          Repairs
        </Typography>
        <Button
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={() => downloadUrl(repairsExportUrl(filters), 'repairs.xlsx')}
        >
          Export XLSX
        </Button>
      </Box>

      <Paper sx={{ p: 2, mb: 2 }}>
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          spacing={2}
          useFlexGap
          sx={{ flexWrap: 'wrap' }}
        >
          <TextField
            label="Customer id"
            type="number"
            value={draft.customer}
            onChange={(event) => updateDraft('customer', event.target.value)}
          />
          <TextField
            label="Vehicle id"
            type="number"
            value={draft.vehicle}
            onChange={(event) => updateDraft('vehicle', event.target.value)}
          />
          <TextField
            label="Start from"
            type="date"
            slotProps={{ inputLabel: { shrink: true } }}
            value={draft.startFrom}
            onChange={(event) => updateDraft('startFrom', event.target.value)}
          />
          <TextField
            label="Start to"
            type="date"
            slotProps={{ inputLabel: { shrink: true } }}
            value={draft.startTo}
            onChange={(event) => updateDraft('startTo', event.target.value)}
          />
          <Button variant="contained" onClick={applyFilters}>
            Apply
          </Button>
          <Button onClick={clearFilters}>Clear</Button>
        </Stack>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {actionError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {actionError}
        </Alert>
      )}

      {loading ? (
        <CircularProgress />
      ) : (
        <TableContainer component={Paper}>
          <Table aria-label="Repairs" sx={{ '& td, & th': { height: 64 } }}>
            <TableHead>
              <TableRow>
                <TableCell>Cliente</TableCell>
                <TableCell>Total hours</TableCell>
                <TableCell>Delivery date</TableCell>
                <TableCell>End date</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(data ?? []).length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5}>No repairs found.</TableCell>
                </TableRow>
              ) : (
                (data ?? []).map((repair) => (
                  <TableRow key={repair.id} hover>
                    <TableCell>{repair.customer_name ?? '—'}</TableCell>
                    <TableCell>{formatHours(repair.total_hours)}</TableCell>
                    <TableCell>{formatDate(repair.delivery_date)}</TableCell>
                    <TableCell>{formatDate(repair.end_data)}</TableCell>
                    <TableCell align="right">
                      <IconButton
                        aria-label={`Open repair ${repair.id}`}
                        onClick={() => navigate(`/repairs/${repair.id}`)}
                      >
                        <ChevronRightIcon />
                      </IconButton>
                      <IconButton
                        color="error"
                        aria-label={`Delete repair ${repair.id}`}
                        onClick={() => setToDelete(repair)}
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
      )}

      <Dialog open={Boolean(toDelete)} onClose={() => setToDelete(null)}>
        <DialogTitle>Delete repair</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Delete repair #{toDelete?.id}? This also removes its work log and parts.
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

export default RepairsListPage
