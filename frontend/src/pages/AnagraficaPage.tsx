import { useState } from 'react'
import {
  Alert,
  Box,
  CircularProgress,
  Paper,
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
import { listCustomers, listVehicles } from '../api/reference'
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

function VehiclesList() {
  const { data, error, loading } = useApi(() => listVehicles(), [])
  const [query, setQuery] = useState('')

  const vehicles = data ?? []
  const rows = vehicles.filter((vehicle) =>
    matchesQuery(
      [
        vehicle.targa,
        vehicle.autocarro,
        vehicle.carrozzeria,
        vehicle.modello,
        vehicle.classe,
        vehicle.commessa,
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
                <TableCell>Targa</TableCell>
                <TableCell>Autocarro</TableCell>
                <TableCell>Carrozzeria</TableCell>
                <TableCell>Modello</TableCell>
                <TableCell>Classe</TableCell>
                <TableCell>Commessa</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6}>
                    <Typography color="text.secondary">
                      {vehicles.length === 0 ? 'No allestimenti.' : 'No matches.'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                rows.map((vehicle) => (
                  <TableRow key={vehicle.id}>
                    <TableCell>{cell(vehicle.targa)}</TableCell>
                    <TableCell>{cell(vehicle.autocarro)}</TableCell>
                    <TableCell>{cell(vehicle.carrozzeria)}</TableCell>
                    <TableCell>{cell(vehicle.modello)}</TableCell>
                    <TableCell>{cell(vehicle.classe)}</TableCell>
                    <TableCell>{cell(vehicle.commessa)}</TableCell>
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
