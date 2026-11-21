import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Fab,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import ChevronRightIcon from '@mui/icons-material/ChevronRight'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import { useNavigate } from 'react-router-dom'
import { listRepairs } from '../api/repairs'
import { useApi } from '../hooks/useApi'
import { formatDate, formatHours } from '../lib/format'

function HomePage() {
  const navigate = useNavigate()
  const { data, error, loading } = useApi(() => listRepairs(), [])
  const active = (data ?? []).filter((repair) => !repair.end_data)

  return (
    <Box>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          mb: 2,
        }}
      >
        <Typography variant="h4" component="h1">
          Active repairs
        </Typography>
        <Fab color="primary" aria-label="New repair" onClick={() => navigate('/repairs/new')}>
          <AddIcon />
        </Fab>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <CircularProgress />
      ) : (
        <TableContainer component={Paper}>
          <Table aria-label="Active repairs" sx={{ '& td, & th': { height: 64 } }}>
            <TableHead>
              <TableRow>
                <TableCell>Cliente</TableCell>
                <TableCell>Total hours</TableCell>
                <TableCell>End date</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {active.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4}>No active repairs.</TableCell>
                </TableRow>
              ) : (
                active.map((repair) => (
                  <TableRow key={repair.id} hover>
                    <TableCell>{repair.customer_name ?? '—'}</TableCell>
                    <TableCell>{formatHours(repair.total_hours)}</TableCell>
                    <TableCell>{formatDate(repair.delivery_date)}</TableCell>
                    <TableCell align="right">
                      <IconButton
                        aria-label={`Start work log ${repair.id}`}
                        onClick={() =>
                          navigate(`/repairs/${repair.id}/work-log/new`)
                        }
                      >
                        <PlayArrowIcon />
                      </IconButton>
                      <Button
                        endIcon={<ChevronRightIcon />}
                        aria-label={`Open repair ${repair.id}`}
                        onClick={() => navigate(`/repairs/${repair.id}`)}
                      >
                        Open
                      </Button>
                    </TableCell>
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

export default HomePage
