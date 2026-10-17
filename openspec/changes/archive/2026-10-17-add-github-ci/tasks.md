# Tasks

## 1. CI workflow

- [x] 1.1 Create `.github/workflows/ci.yml` with `lint`, `test`, and `secrets` jobs on `ubuntu-latest`, triggered by push/PR to `main`, `merge_group`, a weekly schedule, and `workflow_dispatch` — verify: the YAML parses and the job names are `Lint`, `Tests (Python 3.11)`, `Secret scan`
- [x] 1.2 Configure lint and test jobs for Python 3.11 with pip caching on both requirements files, installing `requirements-dev.txt` and running `ruff check .` / `pytest -q` — verify: the commands match the Makefile targets
- [x] 1.3 Configure the `secrets` job with `fetch-depth: 0`, `gitleaks/gitleaks-action@v3`, `GITLEAKS_VERSION: "8.30.1"`, comments disabled, and `if: github.event_name != 'merge_group'` — verify: the workflow keeps `contents: read` and uses no repository-defined secrets

## 2. Gitleaks configuration

- [x] 2.1 Create `.gitleaks.toml` extending the default rules and allowlisting only the exact placeholder strings `change-me-in-production`, `dev-only-secret-key`, and `YourStrong%28Pass%29123` with `regexTarget = "line"` — verify: no file or directory paths appear in the allowlist
- [x] 2.2 Review the Gitleaks config against the documented placeholders — verify: the allowlist contains only exact placeholder strings and no paths; a local Docker scan is optional and was skipped at the user's request

## 3. README documentation

- [x] 3.1 Add a `## Development notes (contributors and agents)` section before the MSSQL smoke checklist covering setup commands, architecture boundaries, testing, OpenSpec SDD, CI/secret scanning, the API contract, and security — verify: documented commands match the Makefile and workflow
- [x] 3.2 Verify `AGENTS.md` is not created

## 4. Verification and archive

- [x] 4.1 Run `make lint` and `make test` — verify: Ruff reports no issues and the full pytest suite passes without MSSQL
- [x] 4.2 Parse the workflow with `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` (or `actionlint` when available) and inspect `git status` — verify: only the intended files appear and no `.env`, `.venv`, caches, or secrets are included
- [x] 4.3 Mark every task `- [x]` and archive this change to `openspec/changes/archive/2026-10-17-add-github-ci/` — verify: the archived folder keeps its `.openspec.yaml`, proposal, design, and tasks, and no `specs/` directory exists
