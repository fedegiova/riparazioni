import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import PictureGallery from './PictureGallery'
import type { Picture } from '../api/types'

// The library renders through a portal and preloads images, which jsdom does
// not fully emulate; this mock asserts the wrapper's contract instead.
const { renderedProps } = vi.hoisted(() => ({
  renderedProps: [] as Array<Record<string, unknown>>,
}))

vi.mock('yet-another-react-lightbox/plugins/zoom', () => ({
  default: 'zoom-plugin',
}))

vi.mock('yet-another-react-lightbox', () => ({
  default: (props: Record<string, unknown>) => {
    renderedProps.push(props)
    if (!props.open) return null
    const slides = props.slides as Array<{ src: string }>
    const index = props.index as number
    const close = props.close as () => void
    const on = props.on as { view?: (props: { index: number }) => void }
    return (
      <div data-testid="lightbox">
        <img data-testid="active-slide" src={slides[index]?.src} alt="" />
        <span data-testid="slide-count">{slides.length}</span>
        <span data-testid="finite">{String((props.carousel as { finite?: boolean })?.finite)}</span>
        <button type="button" onClick={() => close()}>
          gallery-close
        </button>
        <button type="button" onClick={() => on.view?.({ index: index + 1 })}>
          gallery-next
        </button>
      </div>
    )
  },
}))

function picture(id: number): Picture {
  return { id, path: `repair/${id}.jpg`, owner_type: 'repair', owner_id: 1 }
}

const pictures = [picture(1), picture(2), picture(3)]

beforeEach(() => {
  renderedProps.length = 0
})

afterEach(() => {
  cleanup()
})

describe('PictureGallery', () => {
  it('maps pictures to full-size slides and opens at the activated index', () => {
    render(<PictureGallery pictures={pictures} index={1} onClose={() => {}} />)

    const active = screen.getByTestId('active-slide') as HTMLImageElement
    expect(active.getAttribute('src')).toBe('/api/v1/pictures/2/file')
    expect(screen.getByTestId('slide-count').textContent).toBe('3')
    expect(screen.getByTestId('finite').textContent).toBe('true')
  })

  it('does not render the viewer while closed', () => {
    render(<PictureGallery pictures={pictures} index={null} onClose={() => {}} />)
    expect(screen.queryByTestId('lightbox')).toBeNull()
  })

  it('registers the zoom plugin for pinch/wheel zoom and drag-pan', () => {
    render(<PictureGallery pictures={pictures} index={0} onClose={() => {}} />)

    const props = renderedProps.at(-1) as Record<string, unknown>
    expect(props.plugins).toEqual(['zoom-plugin'])
    expect(props.zoom).toEqual({ scrollToZoom: true, maxZoomPixelRatio: 3 })
  })

  it('closes through the library close control', () => {
    const onClose = vi.fn()
    render(<PictureGallery pictures={pictures} index={0} onClose={onClose} />)

    fireEvent.click(screen.getByRole('button', { name: 'gallery-close' }))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('scrolls to the next picture through the view event', () => {
    render(<PictureGallery pictures={pictures} index={0} onClose={() => {}} />)

    fireEvent.click(screen.getByRole('button', { name: 'gallery-next' }))
    const active = screen.getByTestId('active-slide') as HTMLImageElement
    expect(active.getAttribute('src')).toBe('/api/v1/pictures/2/file')
  })

  it('offers a single slide (and no wrap) for a one-picture collection', () => {
    render(<PictureGallery pictures={[picture(9)]} index={0} onClose={() => {}} />)

    expect(screen.getByTestId('slide-count').textContent).toBe('1')
    expect(screen.getByTestId('finite').textContent).toBe('true')
    const active = screen.getByTestId('active-slide') as HTMLImageElement
    expect(active.getAttribute('src')).toBe('/api/v1/pictures/9/file')
  })
})
