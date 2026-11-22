// Deep-link smoke check.
//
// Serves the production bundle with `vite preview` and requests each route in
// ROUTES directly, the way a browser does on first load or refresh. For every
// route it extracts the entry document's module script and stylesheet and
// resolves them against that route's URL, then asserts they are served as
// JavaScript / CSS. A relative asset base passes on single-segment routes but
// resolves nested routes under the route (`/repairs/assets/...`) where the SPA
// fallback answers with `index.html` and the app never mounts.
//
// Run with `npm run smoke` (it builds the bundle first).
import { preview } from 'vite'

const ROUTES = [
  '/',
  '/settings',
  '/repairs',
  '/repairs/1',
  '/repairs/new',
  '/repairs/1/work-log/2',
  '/magazzino/bombole/1',
]

function assert(condition, message) {
  if (!condition) throw new Error(message)
}

async function check(origin, route) {
  const pageUrl = new URL(route, origin)
  const pageRes = await fetch(pageUrl)
  assert(pageRes.ok, `${route}: entry document returned ${pageRes.status}`)
  const html = await pageRes.text()
  assert(/<div id="root">/.test(html), `${route}: response is not the app entry document`)

  const scriptSrc = html.match(/<script[^>]*\bsrc="([^"]+)"/)?.[1]
  assert(scriptSrc, `${route}: entry document has no module script`)
  const scriptUrl = new URL(scriptSrc, pageUrl)
  const scriptRes = await fetch(scriptUrl)
  const scriptType = scriptRes.headers.get('content-type') ?? ''
  assert(
    scriptRes.ok && scriptType.includes('javascript'),
    `${route}: module ${scriptUrl.pathname} returned ${scriptRes.status} ${scriptType} (expected JavaScript)`,
  )

  const styleHref = html.match(/<link[^>]*rel="stylesheet"[^>]*\bhref="([^"]+)"/)?.[1]
  if (styleHref) {
    const styleUrl = new URL(styleHref, pageUrl)
    const styleRes = await fetch(styleUrl)
    const styleType = styleRes.headers.get('content-type') ?? ''
    assert(
      styleRes.ok && styleType.includes('css'),
      `${route}: stylesheet ${styleUrl.pathname} returned ${styleRes.status} ${styleType} (expected CSS)`,
    )
  }

  console.log(`✓ ${route} → ${scriptUrl.pathname}`)
}

const server = await preview({
  preview: { host: '127.0.0.1', port: 4273, strictPort: false },
})

try {
  const address = server.httpServer?.address()
  assert(address && typeof address === 'object', 'preview server has no address')
  const origin = `http://127.0.0.1:${address.port}`
  console.log(`Serving the production bundle at ${origin}`)
  for (const route of ROUTES) {
    await check(origin, route)
  }
  console.log('\n✓ Deep-link smoke check passed')
} catch (err) {
  console.error(`\n✗ Deep-link smoke check failed: ${err instanceof Error ? err.message : err}`)
  process.exitCode = 1
} finally {
  await server.close()
}
