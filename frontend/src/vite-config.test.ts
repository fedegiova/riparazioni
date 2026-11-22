// @vitest-environment node
import type { UserConfig } from 'vite'
import { describe, expect, it } from 'vitest'
import viteConfig from '../vite.config'

describe('vite build config', () => {
  it('references built assets from the application root so nested routes load', () => {
    const config = viteConfig as unknown as UserConfig
    expect(config.base).toBe('/')
    expect(config.base).not.toMatch(/^\./)
  })
})
