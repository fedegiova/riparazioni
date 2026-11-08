// Vitest setup: make the jsdom environment behave like a browser for
// relative URLs. Node's undici `Request` (which jsdom does not replace)
// rejects relative URLs such as `/api/v1/vehicles`, while the browser
// `Request` resolves them against the document origin. The app only ever
// issues relative `/api/v1` URLs, so in tests we resolve them against a
// fake origin to mirror the browser.
if (typeof Request !== 'undefined') {
  const NativeRequest = Request
  let relativeWorks = false
  try {
    // eslint-disable-next-line no-new
    new NativeRequest('/probe')
    relativeWorks = true
  } catch {
    relativeWorks = false
  }
  if (!relativeWorks) {
    class RequestWithBase extends NativeRequest {
      constructor(input: RequestInfo | URL, init?: RequestInit) {
        super(
          typeof input === 'string' ? new URL(input, 'http://localhost/') : input,
          init,
        )
      }
    }
    globalThis.Request = RequestWithBase as unknown as typeof NativeRequest
  }
}
