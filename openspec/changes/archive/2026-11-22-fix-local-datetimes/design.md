# Design

## Context

The app is a single-site workshop application. The owned database stores naive
`DATETIME` columns (`REPAIRS.START_DATA`/`END_DATA`, `REPAIR_WORK_LOG.START_TIME`/
`END_TIME`) and the API serializes them with `datetime.isoformat()`, i.e. no
offset. See proposal.md — Why.

The frontend has two halves that disagreed:

- write: `toIso` in `frontend/src/lib/format.ts` parsed a `datetime-local` value
  as local and then `toISOString()`, producing a UTC instant with a `Z` suffix;
  two actions (`archive`, `stop`) skipped the field and used
  `new Date().toISOString()` directly.
- read: `formatDateTime` / `toDateTimeInput` slice the stored string, assuming it
  is already local wall-clock time.

## Goals / Non-Goals

**Goals:**

- The whole repairs/work-log datetime path treats values as local wall-clock
  time, so a value entered and saved is shown back unchanged.
- Server-side defaulting (repair `start_data` when omitted) also produces local
  time.

**Non-Goals:**

- Picture `uploaded_date` and the picture storage-folder date, which are
  unrelated to repair/work-log timestamps.
- Migrating rows already stored shifted; only new writes are corrected.
- Introducing timezone-aware storage or an offset column.

## Decisions

**Store and exchange local wall-clock time, not UTC.**
Chosen over the alternative (keep sending UTC and convert on read) because the
database columns and the read helpers are naive/local by design, the app is
single-site, and the reported symptom is that the written value and the read
value disagree. Keeping UTC would require converting on every read and would
still disagree with the naive storage.

**Serialize `datetime-local` values as naive ISO, normalized to seconds.**
`toIso` returns the field value with `:00` seconds appended when needed
(`2026-11-22T00:07` → `2026-11-22T00:07:00`) and validates the shape, so the API
receives a full ISO datetime and unparseable input still yields `undefined`. It
no longer constructs a `Date` or calls `toISOString()`.

**Centralize "now" writes in `nowIso()`.**
`nowIso()` builds on `nowDateTimeInput()` (already local) and appends `:00`;
`RepairPage` uses it for archive (`end_data`) and stop (`end_time`) instead of
`new Date().toISOString()`.

**Make the repair start default local on the backend.**
`REPAIRS.start_data`'s column default currently returns a naive UTC time, which
is wrong when a client omits `start_data` (the field can be cleared). A dedicated
local-now default is used for `start_data`; the existing UTC `_now` stays for
`uploaded_date` so picture semantics are untouched.

## Risks / Trade-offs

- [Frontend and backend must agree on "local"; they can drift if the server's
  timezone differs from the workshop's] → The frontend always sends an explicit
  start value in normal use, so server defaulting is only a fallback; the app is
  deployed at the site.
- [Existing rows written before the fix remain shifted] → Accepted; the report
  covers new writes, and no backfill is in scope.
- [Losing strict parse validation of an arbitrary string] → The value always
  comes from a `datetime-local` input; `toIso` still returns `undefined` for
  empty input and non-matching shapes.

## Migration Plan

Frontend-only behavior plus a backend default; no schema change, so no data
migration. Deploy the app as usual; rollback is reverting the commit.
