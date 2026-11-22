import { useEffect, useMemo, useState } from 'react'
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
import {
  getRefrigerator,
  listGasCylinders,
  listRefrigerators,
} from '../api/equipment'
import { addWorkLog, getRepair, updateWorkLog } from '../api/repairs'
import { getOperators } from '../api/settings'
import type {
  GasCylinder,
  Refrigerator,
  WorkLogEntry,
  WorkLogInput,
} from '../api/types'
import SearchModal from '../components/SearchModal'
import { useApi } from '../hooks/useApi'
import { toDateTimeInput, nowDateTimeInput, toIso } from '../lib/format'

type GasOperation = 'none' | 'fill' | 'recovery' | 'recovery_recharge'

const OPERATIONS: GasOperation[] = ['none', 'fill', 'recovery', 'recovery_recharge']

const OPERATION_LABELS: Record<GasOperation, string> = {
  none: 'None',
  fill: 'Fill',
  recovery: 'Recovery',
  recovery_recharge: 'Recovery + recharge',
}

function measuredLabel(operation: GasOperation): string {
  if (operation === 'fill') return 'Added gas (kg)'
  if (operation === 'recovery') return 'Recovered gas (kg)'
  return 'Net added gas (kg)'
}

function cylinderLabel(cylinder: GasCylinder): string {
  return cylinder.gas_kind ? `${cylinder.gas_kind} #${cylinder.id}` : `#${cylinder.id}`
}

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
  const [description, setDescription] = useState('')
  const [operators, setOperators] = useState<string[]>([])
  const [loadedEntry, setLoadedEntry] = useState<WorkLogEntry | null>(null)

  const [gasOperation, setGasOperation] = useState<GasOperation>('none')
  const [gasTouched, setGasTouched] = useState(false)
  const [cylinder, setCylinder] = useState<{ id: number; label: string } | null>(null)
  const [measured, setMeasured] = useState('')
  const [cylinderModal, setCylinderModal] = useState(false)

  const [allCylinders, setAllCylinders] = useState<GasCylinder[]>([])
  const [equipment, setEquipment] = useState<Refrigerator | null>(null)

  const [saving, setSaving] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  useEffect(() => {
    if (isNew || !repair) return
    const entry = (repair.work_log ?? []).find(
      (item) => String(item.id) === entryId,
    )
    if (!entry) return
    setLoadedEntry(entry)
    setStartTime(toDateTimeInput(entry.start_time))
    setEndTime(toDateTimeInput(entry.end_time))
    setOperator(entry.operator ?? '')
    setDescription(entry.description ?? '')
    setGasOperation((entry.gas_operation as GasOperation | null) ?? 'none')
    setMeasured(
      entry.gas_measured_kg != null ? String(entry.gas_measured_kg) : '',
    )
    setCylinder(
      entry.gas_recharge != null
        ? { id: entry.gas_recharge, label: `#${entry.gas_recharge}` }
        : null,
    )
    setGasTouched(false)
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

  // Resolve the refrigerator the gas work belongs to and the cylinders on
  // hand. The locked unit wins once the repair has gas work; otherwise the
  // unit installed on the repair's allestimento is used.
  useEffect(() => {
    if (!repair) return
    let active = true
    async function load() {
      const cylinders = await listGasCylinders()
      let fridge: Refrigerator | null = null
      if (repair && repair.refrigerator != null) {
        fridge = await getRefrigerator(repair.refrigerator)
      } else if (repair && repair.vehicle != null) {
        const list = await listRefrigerators(repair.vehicle)
        fridge = list[0] ?? null
      }
      return { cylinders, fridge }
    }
    load()
      .then(({ cylinders, fridge }) => {
        if (!active) return
        setAllCylinders(cylinders)
        setEquipment(fridge)
        // Label a stored cylinder reference once the list is available.
        setCylinder((current) => {
          if (!current) return current
          const match = cylinders.find((item) => item.id === current.id)
          return match ? { id: match.id, label: cylinderLabel(match) } : current
        })
      })
      .catch(() => {
        // Leave the equipment unknown; a gas save is blocked below.
      })
    return () => {
      active = false
    }
  }, [repair])

  const matchingCylinders = useMemo(
    () =>
      equipment
        ? allCylinders.filter((item) => item.gas_kind === equipment.gas_kind)
        : [],
    [allCylinders, equipment],
  )

  const gasSelected = gasOperation !== 'none'
  const storedOperation = loadedEntry?.gas_operation ?? null
  const selectedOperation: GasOperation | null = gasSelected ? gasOperation : null
  // Only touch the stored gas dataset when the operation or a gas field was
  // changed: a metadata-only edit leaves it alone.
  const gasChanged =
    gasTouched || selectedOperation !== storedOperation
  const sendMovement = gasChanged && selectedOperation !== null

  let blocker: string | null = null
  if (gasSelected) {
    if (!repair?.vehicle) {
      blocker =
        'This repair has no allestimento; set its vehicle before recording gas work.'
    } else if (repair.refrigerator != null && repair.refrigerator_installed === false) {
      blocker =
        "The repair's refrigerator was replaced on its allestimento; record gas work for the new unit on a separate repair."
    } else if (!equipment) {
      blocker =
        'No refrigerator is installed on this allestimento; add one in Anagrafica.'
    }
  }

  const nameplate = equipment?.gas_kg ?? null
  const measuredNumber = measured === '' ? null : Number(measured)
  const calculatedRecovered =
    gasOperation === 'recovery_recharge' &&
    nameplate != null &&
    measuredNumber != null &&
    Number.isFinite(measuredNumber)
      ? nameplate - measuredNumber
      : null

  function validateGas(): string | null {
    if (!sendMovement) return null
    if (blocker) return blocker
    if (!cylinder) return 'Select a gas cylinder.'
    if (measuredNumber == null || !Number.isFinite(measuredNumber)) {
      return 'Enter the measured amount in kg.'
    }
    if (gasOperation === 'fill') {
      if (measuredNumber <= 0) return 'The added amount must be positive.'
      if (nameplate != null && measuredNumber > nameplate) {
        return 'The added amount cannot exceed the nameplate capacity.'
      }
    }
    if (gasOperation === 'recovery' && measuredNumber < 0) {
      return 'The recovered amount cannot be negative.'
    }
    if (gasOperation === 'recovery_recharge') {
      if (measuredNumber < 0) return 'The net added amount cannot be negative.'
      if (nameplate != null && measuredNumber > nameplate) {
        return 'The net added amount cannot exceed the nameplate capacity.'
      }
    }
    return null
  }

  async function handleSave() {
    setSaving(true)
    setActionError(null)
    try {
      const gasError = validateGas()
      if (gasError) {
        setActionError(gasError)
        return
      }

      const body: WorkLogInput = {
        start_time: toIso(startTime),
        end_time: toIso(endTime),
        operator: operator || undefined,
        description: description || undefined,
      }

      if (gasChanged) {
        if (selectedOperation === null) {
          // Explicitly switching a saved gas operation to None reverses it.
          body.gas_operation = 'none'
        } else {
          body.gas_operation = selectedOperation
          body.gas_recharge = cylinder?.id ?? null
          body.gas_measured_kg = measuredNumber
          body.expected_refrigerator = equipment?.id ?? undefined
        }
      }

      if (isNew) {
        if (!operator) {
          setActionError('Select a configured operator before saving.')
          return
        }
        await addWorkLog(repairId, { ...body, operator })
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
          {isNew && operators.length === 0 && (
            <Alert severity="warning">
              No operators are configured. Add an operator in Settings before
              creating a work log.
            </Alert>
          )}
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
              {!isNew && <MenuItem value="">None</MenuItem>}
              {operatorOptions.map((name) => (
                <MenuItem key={name} value={name}>
                  {name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            label="Description"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            multiline
            minRows={2}
            fullWidth
          />

          <Stack spacing={2}>
            <FormControl fullWidth>
              <InputLabel id="gas-operation-label">Gas operation</InputLabel>
              <Select
                labelId="gas-operation-label"
                label="Gas operation"
                value={gasOperation}
                onChange={(event) => {
                  setGasTouched(true)
                  setGasOperation(event.target.value as GasOperation)
                }}
              >
                {OPERATIONS.map((operation) => (
                  <MenuItem key={operation} value={operation}>
                    {OPERATION_LABELS[operation]}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {blocker && (
              <Alert severity="warning">{blocker}</Alert>
            )}

            {gasSelected && !blocker && (
              <>
                <Alert severity="info">
                  Refrigerator: {equipment?.serial_nr ?? `#${equipment?.id}`}
                  {nameplate != null ? ` — nameplate ${nameplate} kg` : ''}
                  {equipment?.gas_kind ? ` (${equipment.gas_kind})` : ''}
                </Alert>
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
                  <Button
                    startIcon={<SearchIcon />}
                    onClick={() => setCylinderModal(true)}
                  >
                    Search
                  </Button>
                </Stack>
                <TextField
                  label={measuredLabel(gasOperation)}
                  type="number"
                  value={measured}
                  onChange={(event) => {
                    setGasTouched(true)
                    setMeasured(event.target.value)
                  }}
                  fullWidth
                />
                {gasOperation === 'recovery_recharge' && (
                  <Typography variant="body2" color="text.secondary">
                    Recovered (calculated):{' '}
                    {calculatedRecovered != null
                      ? `${Number(calculatedRecovered.toFixed(2))} kg`
                      : '—'}
                  </Typography>
                )}
              </>
            )}
          </Stack>

          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button onClick={() => navigate(`/repairs/${repairId}`)}>Cancel</Button>
            <Button
              variant="contained"
              onClick={handleSave}
              disabled={
                saving ||
                (sendMovement && Boolean(blocker)) ||
                (isNew && (!operator || operators.length === 0))
              }
            >
              {saving ? 'Saving…' : 'Save'}
            </Button>
          </Box>
        </Stack>
      </Paper>

      <SearchModal
        open={cylinderModal}
        title="Select gas cylinder"
        cacheKey="gas-cylinders"
        load={() => Promise.resolve(matchingCylinders)}
        getKey={(item) => item.id}
        getLabel={(item) => cylinderLabel(item)}
        getSecondary={(item) => item.serial_nr ?? undefined}
        onClose={() => setCylinderModal(false)}
        onSelect={(item) => {
          setGasTouched(true)
          setCylinder({ id: item.id, label: cylinderLabel(item) })
          setCylinderModal(false)
        }}
      />
    </Box>
  )
}

export default WorkLogPage
