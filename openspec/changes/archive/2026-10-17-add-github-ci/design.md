# Design

## Context

See proposal.md for motivation. The project is a Flask 3 / Python 3.11 app
tested entirely on in-memory SQLite (with an attached fake `DATIDBSTORICO`),
so CI needs no MSSQL server or ODBC driver. There is no `.github/` directory
yet. The repository is owned by a personal GitHub account, so gitleaks-action
requires no license.

## Goals / Non-Goals

**Goals:**

- Run Ruff and pytest on every push and pull request to `main`.
- Detect committed secrets on PR/push ranges and across full history.
- Keep the workflow read-only and fork-safe.
- Document the checks and conventions in `README.md`.

**Non-Goals:**

- Deployment, container publishing, coverage upload, release automation.
- CodeQL, Dependabot, PR/issue templates, community files.
- OpenSpec CLI installation or validation in CI.
- Creating `AGENTS.md`.
- Branch protection configuration (manual repository setting).

## Decisions

### 1. Three independent jobs

`lint`, `test`, and `secrets` run in parallel. Lint and tests are separate so
a failure is unambiguous and each can be marked as a required check
independently. All jobs run on `ubuntu-latest` with timeouts (10/15/10
minutes).

### 2. Triggers

`push` and `pull_request` on `main`, plus `merge_group` for merge queues,
a weekly schedule (`0 4 * * 1`), and `workflow_dispatch`. The scheduled and
manual runs are what force Gitleaks to scan the full history; PR/push runs
scan the event's commit range.

### 3. Python 3.11 only, with pip caching

The project targets Python 3.11+; CI pins 3.11, the minimum supported
version. `actions/setup-python` caches pip using both requirements files as
the dependency path.

### 4. Read-only, fork-safe permissions

`permissions: contents: read` applies to the whole workflow. Only the
automatically provided `GITHUB_TOKEN` is used (to read PR commits). Gitleaks
PR comments are disabled (`GITLEAKS_ENABLE_COMMENTS: "false"`) so no
`pull-requests: write` is needed. No repository-defined secrets are
required.

### 5. Gitleaks scan scopes and version pin

`fetch-depth: 0` is set only on the `secrets` job. `GITLEAKS_VERSION` pins
8.30.1. Findings appear in the job log and summary; the action uploads a
SARIF artifact by default. gitleaks-action v3 does not support the
`merge_group` event (it exits 1), so the `secrets` job is gated with
`if: github.event_name != 'merge_group'`.

### 6. Allowlist exact placeholder strings only

`.gitleaks.toml` extends the default rules (`useDefault = true`) and
allowlists `change-me-in-production`, `dev-only-secret-key`, and
`YourStrong%28Pass%29123` with `regexTarget = "line"`. Files and directories
are never allowlisted, so a real secret added to `.env.example`,
`app/config.py`, or `tests/` is still detected. `.gitleaksignore` is reserved
for confirmed false-positive fingerprints.

### 7. Documentation in README, not AGENTS.md

The workflow, local commands, architecture boundaries, testing approach, and
OpenSpec conventions are documented in a new README section. `AGENTS.md` is
intentionally not created.

### 8. No OpenSpec CLI in CI

OpenSpec artifacts are reviewed in the pull request. CI does not install or
run the CLI, and this change has `skip_specs: true` with no `specs/`
directory because it is tooling-only.

## Risks / Trade-offs

- [gitleaks-action requires a license for organizations] → this personal
  repository needs none; transferring it to an organization requires adding
  `GITLEAKS_LICENSE`.
- [Scheduled full-history scan may find an old credential] → rotate the
  credential first; use `.gitleaksignore` only for exact false-positive
  fingerprints.
- [Action major tags may differ from the plan] → `checkout@v7`,
  `setup-python@v7`, and `gitleaks-action@v3` were verified to exist; use the
  latest stable major and note the change if a tag disappears.
- [pyodbc source build] → 5.2.0 publishes CPython 3.11 manylinux wheels; add
  `unixodbc-dev` only if pip falls back to a source build.
- [OpenSpec correctness is not enforced by CI] → reviewers must check
  proposal/design/task consistency.

## Migration Plan

Pure addition: no application, test, migration, or deployment changes.
Rollback is deleting the workflow, the Gitleaks config, and the README
section.

## Open Questions

None.
