# Proposal

## Why

The repository has a working pytest suite and Ruff configuration but no
automated checks: nothing prevents a broken test, a lint error, or a
committed credential from reaching `main`. A CI workflow makes those checks
consistent and fork-safe, and a dedicated secret scan covers both new
commits and old history.

## What Changes

- Add `.github/workflows/ci.yml` with three jobs (`lint`, `test`, `secrets`)
  that run Ruff, pytest on Python 3.11, and a Gitleaks scan on pushes and
  pull requests to `main`.
- Run the Gitleaks job additionally on a weekly schedule and on manual
  dispatch, with full git history (`fetch-depth: 0`), so removed-but-still-
  present secrets are detected.
- Add `.gitleaks.toml` extending the default rules and allowlisting only the
  documented development placeholder values.
- Document the commands, architecture boundaries, testing approach,
  OpenSpec workflow, and CI/secret-scan behavior in `README.md`.
- Record this tooling-only work as an OpenSpec change with
  `skip_specs: true` (no delta specs).

## Capabilities

### New Capabilities

(none — tooling and documentation only)

### Modified Capabilities

(none)

## Impact

- **Code**: no application, test, or migration changes.
- **CI**: new workflow using only the automatically provided `GITHUB_TOKEN`
  with `contents: read`; no repository-defined secrets.
- **Documentation**: new README section; no `AGENTS.md` is created.
- **Non-goals**: deployment/CD, container publishing, coverage upload,
  release automation, CodeQL, Dependabot, PR/issue templates, community
  files, OpenSpec CLI execution in CI, and branch protection configuration.
