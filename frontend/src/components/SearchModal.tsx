import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Alert,
  Box,
  CircularProgress,
  Dialog,
  DialogContent,
  DialogTitle,
  List,
  ListItemButton,
  ListItemText,
  TextField,
  Typography,
} from '@mui/material'

// Loaded reference lists live for the session; the modal caps rendered matches
// so a multi-thousand-row list never lands in the DOM at once.
const cache = new Map<string, unknown[]>()

export type SearchModalProps<T> = {
  open: boolean
  title: string
  cacheKey: string
  load: () => Promise<T[]>
  getKey: (item: T) => number | string
  getLabel: (item: T) => string
  getSecondary?: (item: T) => string | undefined
  onClose: () => void
  onSelect: (item: T) => void
}

export function SearchModal<T>({
  open,
  title,
  cacheKey,
  load,
  getKey,
  getLabel,
  getSecondary,
  onClose,
  onSelect,
}: SearchModalProps<T>) {
  const [items, setItems] = useState<T[] | null>(
    () => (cache.get(cacheKey) as T[] | undefined) ?? null,
  )
  const [query, setQuery] = useState('')
  const [error, setError] = useState<string | null>(null)
  const loadRef = useRef(load)
  loadRef.current = load

  useEffect(() => {
    if (!open || items) return
    let active = true
    loadRef.current()
      .then((result) => {
        cache.set(cacheKey, result)
        if (active) setItems(result)
      })
      .catch((err: unknown) => {
        if (active) setError(err instanceof Error ? err.message : 'Unexpected error')
      })
    return () => {
      active = false
    }
  }, [open, items, cacheKey])

  const matches = useMemo(() => {
    if (!items) return []
    const needle = query.trim().toLowerCase()
    const found = needle
      ? items.filter((item) =>
          [getLabel(item), getSecondary?.(item) ?? '']
            .join(' ')
            .toLowerCase()
            .includes(needle),
        )
      : items
    return found.slice(0, 50)
  }, [items, query, getLabel, getSecondary])

  const truncated = items ? (query.trim() ? matches.length >= 50 : items.length > 50) : false

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <TextField
          autoFocus
          fullWidth
          label="Search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          sx={{ my: 1 }}
        />
        {error && <Alert severity="error">{error}</Alert>}
        {!items && !error && (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
            <CircularProgress />
          </Box>
        )}
        {items && (
          <>
            {truncated && (
              <Typography variant="body2" color="text.secondary">
                Showing the first matches — refine your search.
              </Typography>
            )}
            <List>
              {matches.map((item) => (
                <ListItemButton key={getKey(item)} onClick={() => onSelect(item)}>
                  <ListItemText primary={getLabel(item)} secondary={getSecondary?.(item)} />
                </ListItemButton>
              ))}
              {matches.length === 0 && (
                <Typography sx={{ p: 2 }} color="text.secondary">
                  No matches.
                </Typography>
              )}
            </List>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}

export default SearchModal
