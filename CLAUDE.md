# Hackathon FIAP Fase 5 — Modelagem de Ameaças com IA (STRIDE)

See @specs/sdd.md for full Software Design Document and @specs/features/ for detailed specs.

---

## Context7 Rule (MANDATORY)

Every code change MUST query the Context7 MCP for current docs, best practices, and examples of any library, framework, SDK, API, or CLI used — including FastAPI, Pydantic, PyTorch, Docker, OpenCV, YOLOv11n, SQLAlchemy. Apply even when knowledge seems obvious; training data may be stale. Prefer Context7 over Web Search for technical docs.

## Domain Context

**Company**: FIAP Software Security.
**Goal**: Automatically perform STRIDE threat modeling from software architecture diagram images.
**Pipeline**: Upload image → Detect components (YOLOv11n) → Apply STRIDE → Lookup CVEs/CWEs → Generate report.

**STRIDE categories**:
- S = Spoofing (Authentication)
- T = Tampering (Integrity)
- R = Repudiation (Non-repudiation)
- I = Information Disclosure (Confidentiality)
- D = Denial of Service (Availability)
- E = Elevation of Privilege (Authorization)

## Tech Stack

- Python 3.11+, FastAPI + Pydantic v2, SQLAlchemy 2.0 + asyncpg + Alembic
- OpenCV + YOLOv11 (Ultralytics) + PyTorch
- PostgreSQL 17, Redis 8
- Docker + Docker Compose
- pytest + httpx (async tests)
- ruff, black, mypy
- Poetry (pyproject.toml)

## Code Style

- Code language: **English** (variables, functions, classes).
- Doc/spec language: **Portuguese** (docs, specs, explanatory comments).
- Commits: Portuguese, imperative, [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).
- Type hints mandatory.

## Repository Etiquette (CRITICAL)

`main` is protected. **NEVER commit directly to `main`.**
Every change goes through:
1. Branch `feature/nome-da-spec` (e.g., `feature/001-api-core-scaffolding`)
2. Pull Request to `main`
3. Review + CI green before merge

## Project Conventions

- Clean Architecture / Ports and Adapters: decouple domain from frameworks.
- API First: define OpenAPI contracts before implementing endpoints.
- Security by Default: rate limiting, input validation, OWASP headers (CSP, HSTS, X-Content-Type-Options, X-Frame-Options) on every route from day one.
- Privacy by Design: anonymize/pseudonymize sensitive data before logging or persistence (LGPD).
- Observability: structured JSON logging with `timestamp`, `level`, `module`, `message`, `request_id`.
- File uploads: validate by magic bytes (PNG, JPG, JPEG); max 50MB.
- Model artifacts (`best.pt`, `best.onnx`): store in `models/`; do not version large binaries in git.
- CI gates: ruff + mypy + 70% test coverage must pass before any PR can be merged.

## Architecture Decisions

- YOLOv11n as detection backbone (speed over accuracy for MVP; upgrade to s/m if needed).
- ONNX Runtime for production inference; PyTorch `.pt` kept for retraining.
- STRIDE engine is rule-based (YAML mappings), not LLM-driven, for determinism and speed.
- Vulnerability lookup uses local YAML DB as primary source; NVD API as optional enhancement.
- Markdown as primary report format; HTML/PDF optional.

## Useful Links

- [Fase 1](https://github.com/vagnerbarbosa/tech-challenge-fase-1) | [Fase 2](https://github.com/vagnerbarbosa/tech-challenge-fase-2) | [Fase 3](https://github.com/vagnerbarbosa/tech-challenge-fase-3) | [Fase 4](https://github.com/vagnerbarbosa/tech-challenge-fase-4) | [Fase 5 (this)](https://github.com/vagnerbarbosa/hackathon-fiap-fase-5)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [OWASP Cheat Sheets](https://cheatsheetseries.owasp.org/)
- [NVD — National Vulnerability Database](https://nvd.nist.gov/)
- [STRIDE — Microsoft](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats)
