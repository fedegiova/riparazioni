import { useEffect, useRef, useState, type ChangeEvent } from 'react'
import { Alert, Box, Button, IconButton, Typography } from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import DeleteIcon from '@mui/icons-material/Delete'
import {
  deletePicture,
  listPictures,
  pictureThumbnailUrl,
  uploadPicture,
  type PictureOwnerType,
} from '../api/pictures'
import type { Picture } from '../api/types'
import PictureGallery from './PictureGallery'

type PictureSectionProps = {
  ownerType: PictureOwnerType
  ownerId: number
  /**
   * Pictures the caller already has (e.g. the repair detail). When set, the
   * section seeds from it and makes no request; pass a stable reference.
   */
  initialPictures?: Picture[]
  /** Heading text; omitted inside a dialog whose own title already says it. */
  title?: string
}

/**
 * Capture, list, delete, and view the pictures of one owner.
 *
 * The capture control is a hidden file input (`accept="image/*"`,
 * `capture="environment"`) so the device camera opens without a filename
 * prompt. Thumbnails load from the minified view; activating one opens the
 * full-screen gallery on the full-size file.
 */
function PictureSection({
  ownerType,
  ownerId,
  initialPictures,
  title,
}: PictureSectionProps) {
  const [pictures, setPictures] = useState<Picture[]>(initialPictures ?? [])
  const [error, setError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [galleryIndex, setGalleryIndex] = useState<number | null>(null)
  const input = useRef<HTMLInputElement>(null)
  // Latest caller-provided list, kept in a ref so the seed effect can read it
  // without listing it as a dependency (a fresh array each render would
  // otherwise re-seed in a loop).
  const initialRef = useRef(initialPictures)
  useEffect(() => {
    initialRef.current = initialPictures
  })

  // Seed from the caller's list when provided; otherwise fetch on demand. Only
  // re-runs when the owner changes.
  useEffect(() => {
    if (initialRef.current !== undefined) {
      setPictures(initialRef.current)
      return
    }
    let active = true
    listPictures(ownerType, ownerId)
      .then((loaded) => {
        if (active) setPictures(loaded)
      })
      .catch((err) => {
        if (active) setError(err instanceof Error ? err.message : 'Unexpected error')
      })
    return () => {
      active = false
    }
  }, [ownerType, ownerId])

  async function handleSelected(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return
    setUploading(true)
    setError(null)
    try {
      const picture = await uploadPicture(file, ownerType, ownerId)
      setPictures((current) => [...current, picture])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unexpected error')
    } finally {
      setUploading(false)
      // Clear only AFTER the upload has read the File: resetting the input
      // earlier can invalidate the blob on mobile browsers, failing the fetch.
      if (input.current) input.current.value = ''
    }
  }

  async function handleDelete(id: number) {
    setError(null)
    try {
      await deletePicture(id)
      setPictures((current) => current.filter((picture) => picture.id !== id))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unexpected error')
    }
  }

  return (
    <Box>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: title ? 'space-between' : 'flex-end',
          mb: 1,
        }}
      >
        {title && <Typography variant="h6">{title}</Typography>}
        <Button
          startIcon={<AddIcon />}
          onClick={() => input.current?.click()}
          disabled={uploading}
        >
          Add picture
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 1 }}>
          {error}
        </Alert>
      )}

      <input
        ref={input}
        type="file"
        accept="image/*"
        capture="environment"
        data-testid="picture-input"
        style={{ display: 'none' }}
        onChange={handleSelected}
      />

      {pictures.length === 0 ? (
        <Typography color="text.secondary">No pictures.</Typography>
      ) : (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {pictures.map((picture, index) => (
            <Box key={picture.id} sx={{ position: 'relative' }}>
              <Box
                component="img"
                src={pictureThumbnailUrl(picture.id)}
                alt={`Picture ${picture.id}`}
                onClick={() => setGalleryIndex(index)}
                sx={{
                  width: 120,
                  height: 120,
                  objectFit: 'cover',
                  borderRadius: 1,
                  cursor: 'pointer',
                }}
              />
              <IconButton
                color="error"
                size="small"
                aria-label={`Delete picture ${picture.id}`}
                onClick={() => handleDelete(picture.id)}
                sx={{ position: 'absolute', top: 0, right: 0 }}
              >
                <DeleteIcon fontSize="small" />
              </IconButton>
            </Box>
          ))}
        </Box>
      )}

      <PictureGallery
        pictures={pictures}
        index={galleryIndex}
        onClose={() => setGalleryIndex(null)}
      />
    </Box>
  )
}

export default PictureSection
