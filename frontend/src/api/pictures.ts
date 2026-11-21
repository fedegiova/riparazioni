// Data access for pictures. A picture belongs to exactly one owner
// (a repair, spare, or gas cylinder) and is always uploaded already attached.
import { api } from './client'
import type { Picture } from './types'

export type PictureOwnerType = 'repair' | 'spare' | 'cylinder'

// The generated client models the multipart body as its documented object;
// the runtime body is a real FormData, which openapi-fetch passes through.
type PictureUploadBody = {
  file: string
  owner_type: PictureOwnerType
  owner_id: number
  uploaded_by?: string
}

/**
 * Read a picked/captured file into an in-memory File.
 *
 * Firefox for Android can hand over a camera photo backed by a `content://`
 * URI that fails when streamed straight into `fetch` (Chrome copies the bytes
 * into a blob first, which is why it works there). Materializing the bytes
 * first makes the request body an ordinary in-memory blob. The fallback name
 * also covers cameras that send an empty filename.
 *
 * Some Firefox-for-Android builds resolve `File.arrayBuffer()` to an empty
 * buffer (or reject it) for these `content://` files. Returning the original
 * File in that case would reintroduce the streaming failure, so fall back to
 * `FileReader` and fail loudly when neither path yields bytes.
 */
async function readFileBytes(file: File): Promise<ArrayBuffer> {
  try {
    const bytes = await file.arrayBuffer()
    if (bytes.byteLength > 0) return bytes
  } catch {
    // Fall through to FileReader: some Android builds read the content://
    // stream through FileReader even when arrayBuffer() fails.
  }

  return await new Promise<ArrayBuffer>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result
      if (result instanceof ArrayBuffer && result.byteLength > 0) {
        resolve(result)
      } else {
        reject(new Error('The photo could not be read. Please take it again.'))
      }
    }
    reader.onerror = () => {
      reject(new Error('The photo could not be read. Please take it again.'))
    }
    reader.readAsArrayBuffer(file)
  })
}

async function materializeFile(file: File): Promise<File> {
  const bytes = await readFileBytes(file)
  return new File([bytes], file.name || 'photo.jpg', {
    type: file.type || 'image/jpeg',
  })
}

export async function uploadPicture(
  file: File,
  ownerType: PictureOwnerType,
  ownerId: number,
  uploadedBy?: string,
): Promise<Picture> {
  const upload = await materializeFile(file)
  const form = new FormData()
  // The filename is always set so the multipart part is never parsed as a
  // form field (some device cameras send an empty filename).
  form.append('file', upload, upload.name || 'photo.jpg')
  form.append('owner_type', ownerType)
  form.append('owner_id', String(ownerId))
  if (uploadedBy) form.append('uploaded_by', uploadedBy)

  const { data } = await api.POST('/api/v1/pictures', {
    body: form as unknown as PictureUploadBody,
  })
  return data as Picture
}

export async function listPictures(
  ownerType: PictureOwnerType,
  ownerId: number,
): Promise<Picture[]> {
  const { data } = await api.GET('/api/v1/pictures', {
    params: { query: { owner_type: ownerType, owner_id: ownerId } },
  })
  return data ?? []
}

export async function deletePicture(id: number): Promise<void> {
  await api.DELETE('/api/v1/pictures/{picture_id}', {
    params: { path: { picture_id: id } },
  })
}

/** Same-origin URL that serves the stored file bytes. */
export function pictureFileUrl(id: number): string {
  return `/api/v1/pictures/${id}/file`
}

/** Same-origin URL that serves the picture's minified view. */
export function pictureThumbnailUrl(id: number): string {
  return `/api/v1/pictures/${id}/thumbnail`
}
