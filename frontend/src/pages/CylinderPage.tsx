import {
  Alert,
  Box,
  CircularProgress,
  Link,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import { Link as RouterLink, useParams } from 'react-router-dom'
import { getCylinderOperations, getGasCylinder } from '../api/equipment'
import type { CylinderOperation } from '../api/types'
import { useApi } from '../hooks/useApi'
import { formatDateTime } from '../lib/format'

const KIND_LABELS: Record<string, string> = {
  refill: 'Refill',
  recharge: 'Recharge',
  recovery: 'Recovery',
  recovery_recharge: 'Recovery + recharge',
}

function formatWeight(value: number | null | undefined): string {
  if (value == null) return '—'
  return String(Number(value.toFixed(2)))
}

function operationDetails(operation: CylinderOperation): string {
  const parts: string[] = []
  if (operation.recharged_weight != null) {
    parts.push(`Recharged ${formatWeight(operation.recharged_weight)} kg`)
  }
  if (operation.recovered_weight != null) {
    parts.push(`Recovered ${formatWeight(operation.recovered_weight)} kg`)
  }
  return parts.length > 0 ? parts.join(', ') : '—'
}

function CylinderPage() {
  const { id } = useParams<{ id: string }>()
  const cylinderId = Number(id)

  const { data, error, loading } = useApi(
    () =>
      Promise.all([
        getGasCylinder(cylinderId),
        getCylinderOperations(cylinderId),
      ]).then(([cylinder, operations]) => ({ cylinder, operations })),
    [cylinderId],
  )

  if (loading) return <CircularProgress />

  if (error || !data) {
    return <Alert severity="error">{error ?? 'Cylinder not found'}</Alert>
  }

  const { cylinder, operations } = data

  return (
    <Box>
      <Typography variant="h4" component="h1" sx={{ mb: 2 }}>
        Bombola {cylinder.serial_nr ?? `#${cylinder.id}`}
      </Typography>

      <Paper sx={{ p: 2, mb: 2 }}>
        <Stack direction="row" spacing={3} sx={{ flexWrap: 'wrap' }}>
          <Typography variant="body2">Gas: {cylinder.gas_kind ?? '—'}</Typography>
          <Typography variant="body2">Serial: {cylinder.serial_nr ?? '—'}</Typography>
          <Typography variant="body2">Model: {cylinder.model ?? '—'}</Typography>
          <Typography variant="body2">
            {formatWeight(cylinder.remaining_weight)} /{' '}
            {formatWeight(cylinder.full_weight)} kg
          </Typography>
          <Typography variant="body2">
            {cylinder.archived ? 'Archived' : 'Active'}
          </Typography>
        </Stack>
      </Paper>

      <Typography variant="h6" sx={{ mb: 1 }}>
        Operations
      </Typography>
      <TableContainer component={Paper}>
        <Table size="small" aria-label="Operation log">
          <TableHead>
            <TableRow>
              <TableCell>Date</TableCell>
              <TableCell>Operation</TableCell>
              <TableCell>Details</TableCell>
              <TableCell>Remaining</TableCell>
              <TableCell>Reference</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {operations.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5}>
                  <Typography color="text.secondary">No operations.</Typography>
                </TableCell>
              </TableRow>
            ) : (
              operations.map((operation, index) => (
                <TableRow key={`${operation.kind}-${operation.id ?? index}`}>
                  <TableCell>{formatDateTime(operation.date)}</TableCell>
                  <TableCell>{KIND_LABELS[operation.kind] ?? operation.kind}</TableCell>
                  <TableCell>{operationDetails(operation)}</TableCell>
                  <TableCell>
                    {operation.remaining_weight != null
                      ? `${formatWeight(operation.remaining_weight)} kg`
                      : '—'}
                  </TableCell>
                  <TableCell>
                    {operation.kind === 'refill' ? (
                      operation.reference ?? '—'
                    ) : operation.repair_id != null ? (
                      <Link
                        component={RouterLink}
                        to={`/repairs/${operation.repair_id}`}
                      >
                        Repair #{operation.repair_id}
                      </Link>
                    ) : (
                      '—'
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}

export default CylinderPage
