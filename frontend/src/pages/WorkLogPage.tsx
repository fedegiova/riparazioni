import { useEffect, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import SearchIcon from '@mui/icons-material/Search'
import { useNavigate, useParams } from 'react-router-dom'
import { listGasCylinders } from '../api/equipment'
import { addWorkLog, getRepair, updateWorkLog } from '../api/repairs'
import { getOperators } from '../api/settings'
import type { WorkLogInput } from '../api/types'
import SearchModal from '../components/SearchModal'
import { useApi } from '../hooks/useApi'
import { toDateTimeInput, nowDateTimeInput, toIso } from '../lib/format'

type GasState = 'VUOTO' | 'PIENO' | 'RECUPERO' | 'RICUPERO_RICARICA'

function WorkLogPage() {
  const navigate = useNavigate()
  const { id, entryId } = useParams<{ id: string; entryId: string }>()
  const repairId = Number(id)
  const isNew = entryId === 'new'

  const { data: repair, error: loadError, loading } = useApi(
    () => getRepair(repairId),
    [repairId],
  )

  const [startTime, setStartTime] = useState(nowDateTimeInput)
  const [endTime, setEndTime] = useState('')
  const [operator, setOperator] = useState('')
  const [operators, setOperators] = useState<string[]>([])
  const [gasOn, setGasOn] = useState(false)
  const [gasState, setGasState] = useState<'' | GasState>('')
  const [cylinder, setCylinder] = useState<{ id: number; label: string } | null>(null)
  const [rechargeWeight, setRechargeWeight] = useState('')
  const [recoveredWeight, setRecoveredWeight] = useState('')
  const [cylinderModal, setCylinderModal] = useState(false)
  const [saving, setSaving] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  useEffect(() => {
    if (isNew || !repair) return
    const entry = (repair.work_log ?? []).find(
      (item) => String(item.id) === entryId,
    )
    if (!entry) return
    setStartTime(toDateTimeInput(entry.start_time))
    setEndTime(toDateTimeInput(entry.end_time))
    setOperator(entry.operator ?? '')
    const hasGas = Boolean(
      entry.gas_system_state || entry.gas_recharge || entry.gas_recharge_weight,
    )
    setGasOn(hasGas)
    setGasState(entry.gas_system_state ?? '')
    setCylinder(
      entry.gas_recharge != null
        ? { id: entry.gas_recharge, label: `#${entry.gas_recharge}` }
        : null,
    )
    setRechargeWeight(
      entry.gas_recharge_weight != null ? String(entry.gas_recharge_weight) : '',
    )
    setRecoveredWeight(
      entry.gas_recovered_weight != null ? String(entry.gas_recovered_weight) : '',
    )
  }, [isNew, repair, entryId])

  useEffect(() => {
    let active = true
    getOperators()
      .then((names) => {
        if (active) setOperators(names)
      })
      .catch(() => {
        // Fall back to a free-text field when settings are unavailable.
      })
    return () => {
      active = false
    }
  }, [])

  async function handleSave() {
    setSaving(true)
    setActionError(null)
    try {
      const body: WorkLogInput = {
        start_time: toIso(startTime),
        end_time: toIso(endTime),
        operator: operator || undefined,
      }
      if (gasOn) {
        body.gas_system_state = gasState || null
        body.gas_recharge = cylinder?.id ?? null
        body.gas_recharge_weight = rechargeWeight ? Number(rechargeWeight) : null
        body.gas_recovered_weight = recoveredWeight ? Number(recoveredWeight) : null
      }
      if (isNew) {
        await addWorkLog(repairId, body)
      } else {
        await updateWorkLog(repairId, Number(entryId), body)
      }
      navigate(`/repairs/${repairId}`)
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Unexpected error')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <CircularProgress />

  if (loadError) return <Alert severity="error">{loadError}</Alert>

  // Keep an entry's stored operator selectable even when it is not in settings.
  const operatorOptions =
    operator && !operators.includes(operator)
      ? [...operators, operator]
      : operators

  return (
    <Box>
      <Typography variant="h4" component="h1" sx={{ mb: 2 }}>
        {isNew ? 'New work log' : `Work log #${entryId}`}
      </Typography>

      {actionError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {actionError}
        </Alert>
      )}

      <Paper sx={{ p: 2, mb: 2 }}>
        <Stack spacing={2}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField
              label="Start time"
              type="datetime-local"
              value={startTime}
              onChange={(event) => setStartTime(event.target.value)}
              fullWidth
              slotProps={{ inputLabel: { shrink: true } }}
            />
            <TextField
              label="End time"
              type="datetime-local"
              value={endTime}
              onChange={(event) => setEndTime(event.target.value)}
              fullWidth
              slotProps={{ inputLabel: { shrink: true } }}
            />
          </Stack>
          {operators.length > 0 ? (
            <FormControl fullWidth>
              <InputLabel id="operator-label" shrink>
                Operator
              </InputLabel>
              <Select
                labelId="operator-label"
                label="Operator"
                displayEmpty
                value={operator}
                onChange={(event) => setOperator(event.target.value)}
              >
                <MenuItem value="">None</MenuItem>
                {operatorOptions.map((name) => (
                  <MenuItem key={name} value={name}>
                    {name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          ) : (
            <TextField
              label="Operator"
              value={operator}
              onChange={(event) => setOperator(event.target.value)}
              fullWidth
            />
          )}

          <Box>
            <Button
              variant={gasOn ? 'contained' : 'outlined'}
              onClick={() => setGasOn((current) => !current)}
            >
              {gasOn ? 'Gas recharge (on)' : 'Add gas recharge'}
            </Button>
          </Box>

          {gasOn && (
            <Stack spacing={2}>
              <FormControl fullWidth>
                <InputLabel id="gas-state-label">Gas system state</InputLabel>
                <Select
                  labelId="gas-state-label"
                  label="Gas system state"
                  value={gasState}
                  onChange={(event) => setGasState(event.target.value as '' | GasState)}
                >
                  <MenuItem value="VUOTO">VUOTO</MenuItem>
                  <MenuItem value="PIENO">PIENO</MenuItem>
                  <MenuItem value="RECUPERO">RECUPERO</MenuItem>
                  <MenuItem value="RICUPERO_RICARICA">RICUPERO_RICARICA</MenuItem>
                </Select>
              </FormControl>
              <Stack
                direction={{ xs: 'column', sm: 'row' }}
                spacing={1}
                sx={{ alignItems: { sm: 'center' } }}
              >
                <TextField
                  label="Gas cylinder"
                  value={cylinder?.label ?? ''}
                  fullWidth
                  slotProps={{ htmlInput: { readOnly: true } }}
                />
                <Button startIcon={<SearchIcon />} onClick={() => setCylinderModal(true)}>
                  Search
                </Button>
              </Stack>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                <TextField
                  label="Recharge weight (kg)"
                  type="number"
                  value={rechargeWeight}
                  onChange={(event) => setRechargeWeight(event.target.value)}
                  fullWidth
                />
                <TextField
                  label="Recovered weight (kg)"
                  type="number"
                  value={recoveredWeight}
                  onChange={(event) => setRecoveredWeight(event.target.value)}
                  fullWidth
                />
              </Stack>
            </Stack>
          )}

          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button onClick={() => navigate(`/repairs/${repairId}`)}>Cancel</Button>
            <Button variant="contained" onClick={handleSave} disabled={saving}>
              {saving ? 'Saving…' : 'Save'}
            </Button>
          </Box>
        </Stack>
      </Paper>

      <SearchModal
        open={cylinderModal}
        title="Select gas cylinder"
        cacheKey="gas-cylinders"
        load={listGasCylinders}
        getKey={(item) => item.id}
        getLabel={(item) =>
          item.gas_kind ? `${item.gas_kind} #${item.id}` : `Cylinder #${item.id}`
        }
        getSecondary={(item) => item.serial_nr ?? undefined}
        onClose={() => setCylinderModal(false)}
        onSelect={(item) => {
          setCylinder({
            id: item.id,
            label: item.gas_kind ? `${item.gas_kind} #${item.id}` : `#${item.id}`,
          })
          setCylinderModal(false)
        }}
      />
    </Box>
  )
}

export default WorkLogPage
