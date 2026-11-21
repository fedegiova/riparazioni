import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import DeleteIcon from '@mui/icons-material/Delete'
import {
  WEEKDAYS,
  listSettings,
  parseHolidays,
  parseOperators,
  parseWorkingHours,
  putSettings,
  serializeHolidays,
  serializeOperators,
  serializeWorkingHours,
  type HolidayRange,
  type Holidays,
  type Operators,
  type Weekday,
  type WorkingHours,
} from '../api/settings'
import { useApi } from '../hooks/useApi'

function SettingsPage() {
  const { data, error, loading } = useApi(() => listSettings(), [])

  const [operators, setOperators] = useState<Operators>([])
  const [newOperator, setNewOperator] = useState('')
  const [workingHours, setWorkingHours] = useState<WorkingHours>({})
  const [holidays, setHolidays] = useState<Holidays>({})
  const [currentYear] = useState(() => String(new Date().getFullYear()))
  const [year, setYear] = useState(currentYear)

  const [saving, setSaving] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (!data) return
    setOperators(parseOperators(data.operators))
    setWorkingHours(parseWorkingHours(data.working_hours))
    setHolidays(parseHolidays(data.holidays))
  }, [data])

  const yearOptions = useMemo(() => {
    const years = new Set(Object.keys(holidays))
    years.add(currentYear)
    return [...years].sort((a, b) => b.localeCompare(a))
  }, [holidays, currentYear])

  const ranges = holidays[year] ?? []

  function addOperator() {
    const name = newOperator.trim()
    if (!name) return
    setOperators((current) => [...current, name])
    setNewOperator('')
  }

  function removeOperator(index: number) {
    setOperators((current) => current.filter((_, i) => i !== index))
  }

  function updateInterval(day: Weekday, index: number, bound: 0 | 1, value: string) {
    setWorkingHours((current) => {
      const intervals = [...(current[day] ?? [])]
      const existing = intervals[index]
      if (!existing) return current
      intervals[index] = bound === 0 ? [value, existing[1]] : [existing[0], value]
      return { ...current, [day]: intervals }
    })
  }

  function addInterval(day: Weekday) {
    setWorkingHours((current) => ({
      ...current,
      [day]: [...(current[day] ?? []), ['08:00', '12:00']],
    }))
  }

  function removeInterval(day: Weekday, index: number) {
    setWorkingHours((current) => ({
      ...current,
      [day]: (current[day] ?? []).filter((_, i) => i !== index),
    }))
  }

  function addHolidayRange() {
    setHolidays((current) => ({
      ...current,
      [year]: [
        ...(current[year] ?? []),
        { from: `${year}-01-01`, to: `${year}-01-01`, name: '' },
      ],
    }))
  }

  function updateHolidayRange(index: number, field: keyof HolidayRange, value: string) {
    setHolidays((current) => {
      const list = [...(current[year] ?? [])]
      const existing = list[index]
      if (!existing) return current
      list[index] = { ...existing, [field]: value }
      return { ...current, [year]: list }
    })
  }

  function removeHolidayRange(index: number) {
    setHolidays((current) => ({
      ...current,
      [year]: (current[year] ?? []).filter((_, i) => i !== index),
    }))
  }

  async function handleSave() {
    setSaving(true)
    setActionError(null)
    setSaved(false)
    try {
      await putSettings({
        operators: serializeOperators(operators),
        working_hours: serializeWorkingHours(workingHours),
        holidays: serializeHolidays(holidays),
      })
      setSaved(true)
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Unexpected error')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <CircularProgress />

  if (error) return <Alert severity="error">{error}</Alert>

  return (
    <Box>
      <Typography variant="h4" component="h1" sx={{ mb: 2 }}>
        Settings
      </Typography>

      {actionError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {actionError}
        </Alert>
      )}
      {saved && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Settings saved.
        </Alert>
      )}

      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" component="h2" sx={{ mb: 2 }}>
          Operators
        </Typography>
        <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: 'wrap', mb: 2 }}>
          {operators.length === 0 ? (
            <Typography color="text.secondary">No operators.</Typography>
          ) : (
            operators.map((name, index) => (
              <Chip
                key={`${name}-${index}`}
                label={name}
                onDelete={() => removeOperator(index)}
              />
            ))
          )}
        </Stack>
        <Stack direction="row" spacing={1}>
          <TextField
            label="Add operator"
            size="small"
            value={newOperator}
            onChange={(event) => setNewOperator(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                event.preventDefault()
                addOperator()
              }
            }}
          />
          <Button startIcon={<AddIcon />} onClick={addOperator}>
            Add
          </Button>
        </Stack>
      </Paper>

      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" component="h2" sx={{ mb: 2 }}>
          Working hours
        </Typography>
        <Stack spacing={2}>
          {WEEKDAYS.map((day) => (
            <Box key={day}>
              <Typography sx={{ textTransform: 'capitalize', mb: 1 }}>{day}</Typography>
              <Stack spacing={1}>
                {(workingHours[day] ?? []).map((interval, index) => (
                  <Stack
                    key={index}
                    direction="row"
                    spacing={1}
                    sx={{ alignItems: 'center' }}
                  >
                    <TextField
                      type="time"
                      size="small"
                      label="From"
                      value={interval[0]}
                      slotProps={{ inputLabel: { shrink: true } }}
                      onChange={(event) =>
                        updateInterval(day, index, 0, event.target.value)
                      }
                    />
                    <TextField
                      type="time"
                      size="small"
                      label="To"
                      value={interval[1]}
                      slotProps={{ inputLabel: { shrink: true } }}
                      onChange={(event) =>
                        updateInterval(day, index, 1, event.target.value)
                      }
                    />
                    <IconButton
                      aria-label={`Remove ${day} interval ${index + 1}`}
                      onClick={() => removeInterval(day, index)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Stack>
                ))}
                {(workingHours[day] ?? []).length === 0 && (
                  <Typography variant="body2" color="text.secondary">
                    Closed
                  </Typography>
                )}
                <Box>
                  <Button
                    size="small"
                    startIcon={<AddIcon />}
                    onClick={() => addInterval(day)}
                  >
                    Add interval
                  </Button>
                </Box>
              </Stack>
            </Box>
          ))}
        </Stack>
      </Paper>

      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" component="h2" sx={{ mb: 2 }}>
          Holidays
        </Typography>
        <FormControl sx={{ minWidth: 120, mb: 2 }}>
          <InputLabel id="holiday-year-label">Year</InputLabel>
          <Select
            labelId="holiday-year-label"
            label="Year"
            value={year}
            onChange={(event) => setYear(event.target.value)}
          >
            {yearOptions.map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <Stack spacing={1}>
          {ranges.length === 0 && (
            <Typography variant="body2" color="text.secondary">
              No holidays for {year}.
            </Typography>
          )}
          {ranges.map((range, index) => (
            <Stack
              key={index}
              direction={{ xs: 'column', sm: 'row' }}
              spacing={1}
              sx={{ alignItems: { sm: 'center' } }}
            >
              <TextField
                type="date"
                size="small"
                label="From"
                value={range.from}
                slotProps={{ inputLabel: { shrink: true } }}
                onChange={(event) =>
                  updateHolidayRange(index, 'from', event.target.value)
                }
              />
              <TextField
                type="date"
                size="small"
                label="To"
                value={range.to}
                slotProps={{ inputLabel: { shrink: true } }}
                onChange={(event) => updateHolidayRange(index, 'to', event.target.value)}
              />
              <TextField
                size="small"
                label="Name"
                value={range.name}
                onChange={(event) =>
                  updateHolidayRange(index, 'name', event.target.value)
                }
              />
              <IconButton
                aria-label={`Remove holiday ${index + 1}`}
                onClick={() => removeHolidayRange(index)}
              >
                <DeleteIcon />
              </IconButton>
            </Stack>
          ))}
          <Box>
            <Button startIcon={<AddIcon />} onClick={addHolidayRange}>
              Add holiday
            </Button>
          </Box>
        </Stack>
      </Paper>

      <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
        <Button variant="contained" onClick={handleSave} disabled={saving}>
          {saving ? 'Saving…' : 'Save'}
        </Button>
      </Box>
    </Box>
  )
}

export default SettingsPage
