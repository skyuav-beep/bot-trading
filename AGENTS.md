# Repository Guidelines

## Project Structure & Module Organization
- Keep the root lean: `README.md` introduces the trading bot project and `docs/` holds domain knowledge.
- Use `docs/_latest/spec.md` for the working specification, archive signed-off versions under `docs/specs/`, and store diagrams in `docs/_assets/`.
- Runtime code should live under `src/` (create it if missing) with packages such as `data`, `strategies`, and `execution`; mirror that layout under `tests/`.
- Update supporting contracts alongside code: `docs/api.yaml` for HTTP surfaces, `docs/schema.sql` for storage, and `docs/requirements.md` for operational notes.

## Build, Test, and Development Commands
- Standard runtime is Python 3.12; bootstrap with `python -m venv .venv && source .venv/bin/activate`.
- Install dependencies via `pip install -r requirements.txt`; summarise rationale in `docs/requirements.md` when adding or upgrading libraries.
- Run the local entry point with `python -m src.cli --config configs/dev.yaml` (adjust module/config names to match your feature).
- Lint and format before committing: `ruff check .` for static analysis and `black .` for formatting.

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation, descriptive type hints, and module docstrings that explain trading assumptions.
- Modules are lowercase with underscores (`src/strategies/mean_reversion.py`), classes use PascalCase, functions and variables use snake_case.
- Configuration files belong in `configs/` and take kebab-case filenames (e.g. `configs/live-mean-reversion.yaml`).

## Testing Guidelines
- Co-locate unit tests under `tests/<package>/test_<module>.py`; put multi-service scenarios in `tests/integration/`.
- Use `pytest -q` for fast feedback and `pytest --cov=src --cov-report=term-missing` to track coverage (target ≥85%).
- Mock broker/exchange access and keep real credentials in ignored `.env.local` files. Document new test cases in `docs/_latest/spec.md`.

## Commit & Pull Request Guidelines
- Write imperative commit subjects (`Add mean reversion strategy`); include context in the body when behavior or risk changes.
- PRs must link to the relevant spec or ticket, list commands run, and attach logs or screenshots of notable outputs.
- Update `docs/CHANGELOG.md` under an `## [Unreleased]` heading for user-visible changes, and ensure reviewers get a clean, rebased branch.

## Documentation & Security Notes
- Never commit secrets; provide sanitized examples in `.env.example` and reference them from the docs.
- When changing interfaces or schemas, update the OpenAPI file, database schema, and requirements notes in the same PR.
- Record trading limits, risk flags, and rollout steps in `docs/_latest/spec.md` so the knowledge base stays audit-ready.
