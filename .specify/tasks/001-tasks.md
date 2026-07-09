# Tasks: API Core + Scaffolding (Spec 001)

**Feature**: 001-api-core-scaffolding | **Branch**: `feature/001-api-core`

---

## Phase 1: Setup — Project Initialization

Setup inicial do projeto com dependências e configurações base.

- [ ] T001 [P] Create `pyproject.toml` with Poetry dependencies (FastAPI, SQLAlchemy, asyncpg, alembic, slowapi, pydantic-settings, pytest, etc.)
- [ ] T002 [P] Create `Dockerfile` multi-stage (builder + runtime) for Python 3.11 slim
- [ ] T003 [P] Create `docker-compose.yml` with services: api (port 8000), db (PostgreSQL 17), redis (Redis 8)
- [ ] T004 [P] Create `.env.example` with all required environment variables (DATABASE_URL, REDIS_URL, STORAGE_PATH, LOG_LEVEL, API_RATE_LIMIT)
- [ ] T005 Create `.dockerignore` with Python/Docker patterns (__pycache__, .venv, .git, etc.)
- [ ] T006 Create `src/` directory structure with all `__init__.py` files

---

## Phase 2: Foundational — Core Configuration

Configurações core que são pré-requisitos para todas as outras funcionalidades.

- [ ] T007 Create `src/core/config.py` with Settings class using pydantic-settings, loading from .env, with required DATABASE_URL validation
- [ ] T008 Create `src/core/logging.py` with JSON logging configuration including timestamp, level, module, message, request_id fields
- [ ] T009 Create `src/infrastructure/database.py` with AsyncEngine creation, async_sessionmaker with expire_on_commit=False, session manager using asynccontextmanager
- [ ] T010 Create `src/models/base.py` with DeclarativeBase (SQLAlchemy 2.0 style)
- [ ] T011 Create `src/infrastructure/storage.py` with LocalFileStorage class for file operations (save, delete, get_path)

---

## Phase 3: Models — Database Entities

Implementação do modelo de dados.

- [ ] T012 Create `src/models/job.py` with Job model using Mapped/mapped_column, JobStatus enum, timestamps with timezone
- [ ] T013 Create Alembic migration for jobs table (`alembic/versions/`)
- [ ] T014 [P] Update `src/models/__init__.py` to export Base, Job, JobStatus

---

## Phase 4: API Core — FastAPI Application

Implementação da aplicação FastAPI com lifespan e injeção de dependências.

- [ ] T015 Create `src/api/dependencies.py` with get_db(), get_settings(), get_storage() generators using Annotated types and Depends
- [ ] T016 Create `src/api/routes/health.py` with GET /health endpoint checking database connectivity, returning JSON with status, version, database, timestamp
- [ ] T017 Create `src/api/routes/threat_model.py` placeholder with empty routes for future specs (POST /analyze, GET /{job_id}, GET /{job_id}/report)
- [ ] T018 Create `src/api/main.py` with FastAPI app using lifespan context manager, including routers (health, threat_model), middleware setup
- [ ] T019 Update `src/api/routes/__init__.py` to export routers

---

## Phase 5: Security — OWASP + Rate Limiting

Implementação de segurança conforme requisitos OWASP.

- [ ] T020 Create `src/core/security.py` with rate limiting using slowapi + Redis backend, security headers middleware (HSTS, X-Content-Type-Options, X-Frame-Options, CSP), fallback in-memory
- [ ] T021 Create magic bytes validation function in `src/core/security.py` for PNG/JPG validation with filename sanitization
- [ ] T022 Create API Key authentication middleware in `src/core/security.py` validating X-API-Key header, excluding /health and /docs
- [ ] T023 Integrate security middleware, rate limiting and API Key auth into `src/api/main.py`

---

## Phase 6: Tests — Unit + Integration

Implementação dos testes conforme TDD.

- [ ] T024 Create `tests/conftest.py` with fixtures: async_client (httpx.AsyncClient), db_session (AsyncSession), override_settings (Settings)
- [ ] T025 Create `tests/unit/test_health.py` with tests for health endpoint (success case returns 200, database connected)
- [ ] T026 Create `tests/integration/test_api_base.py` with tests for database connectivity, upload placeholder
- [ ] T027 [P] Create `tests/unit/test_config.py` with tests for Settings validation (DATABASE_URL required, defaults work)
- [ ] T028 [P] Create `tests/unit/test_security.py` with tests for rate limiting, security headers, and API Key auth

---

## Phase 7: Polish — Final Configuration

Ajustes finais e configurações de qualidade.

- [ ] T029 Create `scripts/setup.sh` for initial setup automation
- [ ] T030 Verify `poetry.lock` generation and create `requirements.txt` export
- [ ] T031 Create placeholder `.github/workflows/ci.yml` for Spec 007
- [ ] T032 Add healthcheck to Dockerfile with curl
- [ ] T033 Update root `README.md` with setup instructions for this spec

---

## Task Summary

| Phase | Tasks | Parallelizable | Focus |
|-------|-------|----------------|-------|
| Phase 1: Setup | 6 | 5 | Project structure |
| Phase 2: Foundational | 5 | 1 | Core config, DB |
| Phase 3: Models | 3 | 1 | Job model, migrations |
| Phase 4: API Core | 5 | 1 | FastAPI app, routes |
| Phase 5: Security | 3 | 0 | OWASP, rate limiting |
| Phase 6: Tests | 5 | 2 | pytest, fixtures |
| Phase 7: Polish | 5 | 0 | Scripts, docs |

**Total Tasks**: 32
**Parallel Tasks**: 10 (marked with [P])
**Sequential Tasks**: 22

---

## Execution Order

```
Phase 1 ───────────────────────────────────────┐
  T001, T002, T003, T004, T005, T006 (T005,T006 after T001) ─┐
                                                              │
Phase 2 ──────────────────────────────────────────────────────┘
  T007 → T008 → T009 → T010 → T011
         │
         └─────────────────────┐
                               │
Phase 3 ───────────────────────┘
  T012 → T013 → T014
            │
            └──────────────────┐
                               │
Phase 4 ───────────────────────┘
  T015 → T016 → T017 → T018 → T019
                      │
                      └──────────┐
                                 │
Phase 5 ─────────────────────────┘
  T020 → T021 → T022
            │
            └────────────────────┐
                                 │
Phase 6 ─────────────────────────┘
  T023 → T024 → T025
  [P] T026, T027
            │
            └────────────────────┐
                                 │
Phase 7 ─────────────────────────┘
  T028 → T029 → T030 → T031 → T032
```

---

## Validation Checklist

Antes de marcar cada fase como completa:

- [ ] **Phase 1**: `docker-compose up --build` inicia sem erros
- [ ] **Phase 2**: Settings carrega de .env, database engine conecta
- [ ] **Phase 3**: Tabela jobs criada no PostgreSQL
- [ ] **Phase 4**: `GET /health` responde 200 com database connected
- [ ] **Phase 5**: Rate limit ativo, headers OWASP presentes
- [ ] **Phase 6**: `pytest` passa com coverage >= 80%
- [ ] **Phase 7**: Documentação atualizada, scripts funcionando

---

*Tasks generated following Spec-Kit workflow*
*Date: 2026-07-09*
