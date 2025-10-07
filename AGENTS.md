# Repository Guidelines

## Project Structure & Module Organization
- Keep the root doc-first; place application packages under `src/` when introduced (루트는 문서 중심, 실행 코드는 `src/`).
- Treat `docs/_latest/spec.md` as the live spec and archive finals in `docs/specs/` (최신 명세는 `docs/_latest/spec.md`, 확정본은 `docs/specs/`).
- Store diagrams in `docs/_assets/` and update `docs/api.yaml`, `docs/schema.sql`, `docs/requirements.md` with related changes (다이어그램은 `docs/_assets/`, 관련 문서는 함께 갱신).
- Mirror production layout under `tests/` such as `tests/strategies/test_mean_reversion.py` (프로덕션 구조를 `tests/`에 반영).

## Build, Test, and Development Commands
- Use Python 3.12 via `python -m venv .venv && source .venv/bin/activate` (Python 3.12 가상환경 생성).
- Install dependencies with `pip install -r requirements.txt` and log rationale in `docs/requirements.md` (의존성 설치 후 근거 기록).
- Launch features through `python -m src.cli --config configs/dev.yaml` when modules exist (모듈 준비 후 해당 명령으로 실행).
- Run `ruff check .` then `black .` before commits (커밋 전 린트·포맷 필수).

## Coding Style & Naming Conventions
- Follow PEP 8: 4-space indent, practical type hints, concise trading docstrings (PEP 8 규칙 준수).
- Modules/packages stay lowercase snake_case; classes use PascalCase; functions and vars use snake_case (네이밍 일관 유지).
- Keep configs in `configs/` with kebab-case filenames such as `configs/live-mean-reversion.yaml` (설정 파일은 케밥 케이스).

## Testing Guidelines
- Co-locate unit tests under `tests/<package>/test_<module>.py`; complex flows go in `tests/integration/` (단위·통합 테스트 분리).
- Use `pytest -q` for quick runs and `pytest --cov=src --cov-report=term-missing` to maintain ≥85% coverage (pytest로 커버리지 관리).
- Mock external brokers/exchanges and keep secrets in ignored `.env.local` files, documenting fixtures in `docs/_latest/spec.md` (외부 의존성 모킹, 시크릿 보호).

## Commit & Pull Request Guidelines
- Write imperative commit subjects like `Add mean reversion strategy` with context in the body when risk shifts (커밋 제목은 명령형, 위험 변화는 본문 기록).
- Link PRs to specs or tickets, list verification commands, and attach key evidence (PR에 명세/티켓·검증 명령·증빙 추가).
- Update `docs/CHANGELOG.md` under `## [Unreleased]` for user-visible changes and keep branches rebased (변경 사항은 체인지로그·리베이스 유지).

## Documentation & Security Notes
- Never commit secrets; provide sanitized samples in `.env.example` and reference them in docs (시크릿은 예시 파일로만 공유).
- Sync API, schema, and requirement docs whenever interface contracts move (인터페이스 변경 시 문서 동기화).
- Record trading limits, risk gates, and rollout steps in `docs/_latest/spec.md` for audit readiness (거래 한도·리스크·배포 단계 기록).
