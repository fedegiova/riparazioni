import { useEffect, useState } from 'react'
import Lightbox from 'yet-another-react-lightbox'
import Zoom from 'yet-another-react-lightbox/plugins/zoom'
import 'yet-another-react-lightbox/styles.css'
import { pictureFileUrl } from '../api/pictures'
import type { Picture } from '../api/types'

type PictureGalleryProps = {
  /** The collection the viewer scrolls through, in display order. */
  pictures: Picture[]
  /** Index to open at, or null when the viewer is closed. */
  index: number | null
  onClose: () => void
}

/**
 * Full-screen picture viewer, built on yet-another-react-lightbox.
 *
 * A thin wrapper so the rest of the app never imports the library directly:
 * it maps pictures to slides (the full-size file), opens at the requested
 * index, and disables wrap-around at the ends. The library provides the close
 * control, keyboard arrows, and swipe; a single picture shows no navigation.
 */
function PictureGallery({ pictures, index, onClose }: PictureGalleryProps) {
  const [current, setCurrent] = useState(index ?? 0)

  // Re-open at the requested picture. The library keeps its own position
  // between opens, so sync whenever the caller asks for an index.
  useEffect(() => {
    if (index !== null) setCurrent(index)
  }, [index])

  return (
    <Lightbox
      open={index !== null}
      index={current}
      close={onClose}
      slides={pictures.map((picture) => ({ src: pictureFileUrl(picture.id) }))}
      carousel={{ finite: true }}
      // Pinch/double-tap/double-click zoom and drag-to-pan; the wheel also
      // zooms on desktop. maxZoomPixelRatio lifts the default 1:1 cap so the
      // image can be magnified up to 3x its native resolution.
      plugins={[Zoom]}
      zoom={{ scrollToZoom: true, maxZoomPixelRatio: 3 }}
      on={{ view: ({ index: viewIndex }) => setCurrent(viewIndex) }}
    />
  )
}

export default PictureGallery
