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
 */
async function materializeFile(file: File): Promise<File> {
  try {
    const bytes = await file.arrayBuffer()
    return new File([bytes], file.name || 'photo.jpg', {
      type: file.type || 'image/jpeg',
    })
  } catch {
    return file
  }
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
