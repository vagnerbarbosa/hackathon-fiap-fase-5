# Spec: API Core + Scaffolding do Projeto

---

## Contexto / Motivação

O projeto precisa de uma base sólida de API REST para expor todos os serviços do MVP de modelagem de ameaças STRIDE. Esta spec foca exclusivamente no scaffolding inicial: estrutura de diretórios, configuração do FastAPI, Pydantic v2, PostgreSQL via SQLAlchemy 2.0, Docker Compose, segurança OWASP, e healthcheck. Não inclui lógica de negócio específica (detecção, STRIDE, relatórios) — essas são responsabilidade das specs filhas.

## Objetivo

Entregar um scaffolding funcional e seguro que servirá de fundação para todas as outras specs. Deve ser possível rodar `docker-compose up` e ter a API respondendo com healthcheck, estrutura de rotas, middlewares de segurança, e banco de dados conectado.

## Requisitos Funcionais (RF)

### RF-01: Estrutura de Diretórios
Criar estrutura padrão do projeto:
```
├── src/
│   ├── api/
│   │   ├── main.py              # Ponto de entrada FastAPI
│   │   ├── routes/
│   │   │   ├── health.py        # GET /health
│   │   │   └── threat_model.py  # Placeholder para specs futuras
│   │   └── dependencies.py      # Injeção de dependências
│   ├── core/
│   │   ├── config.py            # Settings via Pydantic Settings
│   │   ├── security.py          # Headers OWASP, rate limiting, CORS
│   │   └── logging.py           # Logging estruturado (JSON)
│   ├── models/
│   │   ├── base.py              # Base SQLAlchemy 2.0
│   │   └── job.py               # Modelo de job de análise (status, created_at, updated_at)
│   ├── services/
│   │   └── .gitkeep             # Placeholder para specs futuras
│   ├── infrastructure/
│   │   ├── database.py          # Session manager + engine
│   │   └── storage.py           # FileSystem storage para uploads
│   └── workers/
│       └── .gitkeep             # Placeholder para Celery/RQ
├── tests/
│   ├── unit/
│   │   └── test_health.py       # Teste do healthcheck
│   ├── integration/
│   │   └── test_api_base.py     # Testes de conectividade DB + endpoints
│   └── conftest.py              # Fixtures pytest (client async, db session)
├── alembic/
│   └── versions/                # Migrações SQLAlchemy
├── notebooks/
│   └── .gitkeep
├── dataset/
│   └── .gitkeep
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml               # Poetry dependencies
├── .env.example                 # Variáveis de ambiente de exemplo
├── .github/
│   └── workflows/
│       └── ci.yml               # Placeholder — detalhado na Spec 007
└── CLAUDE.md + specs/
```

### RF-02: FastAPI + Pydantic v2
- Aplicar `FastAPI` com `lifespan` para gerenciamento de startup/shutdown.
- Usar `Pydantic v2` para todos os DTOs de request/response.
- Documentação OpenAPI automática em `/docs` (Swagger UI) e `/redoc`.
- Configurar `JSONResponse` com `orjson` para performance.

### RF-03: Configuração via Pydantic Settings
- Classe `Settings` via `pydantic-settings` carregando de `.env`.
- Variáveis obrigatórias:
  - `DATABASE_URL` (PostgreSQL)
  - `REDIS_URL` (opcional, para cache/fila futura)
  - `STORAGE_PATH` (diretório para uploads temporários)
  - `LOG_LEVEL` (INFO, DEBUG, WARNING)
  - `API_RATE_LIMIT` (requisições por minuto)
- Validação: falhar gracefulmente se variáveis obrigatórias estiverem ausentes.

### RF-04: Conexão PostgreSQL + SQLAlchemy 2.0
- Engine com pool de conexões (`AsyncEngine` + `asyncpg`).
- Session manager via `asynccontextmanager`.
- Modelo base com `DeclarativeBase` (SQLAlchemy 2.0 style).
- Tabela inicial: `Job` — representa uma análise em execução:
  ```python
  class JobStatus(str, Enum):
      PENDING = "pending"
      PROCESSING = "processing"
      COMPLETED = "completed"
      FAILED = "failed"
  
  class Job(Base):
      id: UUID (PK)
      status: JobStatus
      input_image_path: str
      output_report_path: str | None
      error_message: str | None
      created_at: datetime
      updated_at: datetime
  ```
- Alembic configurado para migrações.

### RF-05: Segurança OWASP (Herdado Fase 4)
- **Rate Limiting**: `slowapi` ou middleware custom com Redis. Limitar por IP: `API_RATE_LIMIT` req/min.
- **Headers HTTP**:
  - `Strict-Transport-Security` (HSTS)
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Content-Security-Policy`
- **CORS**: configurável via env, default `allow_origins=[]`.
- **Validação de uploads**: magic bytes para PNG/JPG (herdado Fase 4).
- **Sanitização de logs**: nunca logar paths absolutos sensíveis ou tokens.

### RF-06: Healthcheck
- Endpoint `GET /health` retorna:
  ```json
  {
    "status": "healthy",
    "version": "0.1.0",
    "database": "connected",
    "timestamp": "2026-06-21T14:00:00Z"
  }
  ```
- Deve verificar conectividade com PostgreSQL antes de responder "connected".
- Status HTTP: 200 se tudo OK, 503 se DB fora.

### RF-07: Docker + Docker Compose
- `Dockerfile` multi-stage (builder + runtime) para Python 3.11 slim.
- `docker-compose.yml` com serviços:
  - `api`: aplicação FastAPI (porta 8000)
  - `db`: PostgreSQL 17 (volume persistente)
  - `redis`: Redis 8 (para cache/fila — opcional mas recomendado)
- Healthcheck no container `api` via `curl -f http://localhost:8000/health`.
- `.env.example` com valores padrão para desenvolvimento local.

## Requisitos Não-Funcionais (RNF)

### RNF-01: Performance
- Startup da aplicação < 5 segundos.
- Healthcheck responde em < 100ms.

### RNF-02: Testabilidade
- Testes unitários para healthcheck.
- Testes de integração para conexão DB + upload básico.
- Fixtures pytest: `async_client`, `db_session`, `override_settings`.
- Coverage mínimo: 80% neste módulo.

### RNF-03: Observabilidade
- Logging estruturado em JSON (nível INFO em produção, DEBUG em dev).
- Campos obrigatórios no log: `timestamp`, `level`, `module`, `message`, `request_id`.
- Middleware para injetar `request_id` (UUID) em todo request.

### RNF-04: Reprodutibilidade
- `poetry.lock` versionado.
- `requirements.txt` exportado do Poetry para compatibilidade.
- Scripts em `scripts/` para setup inicial (`scripts/setup.sh`).

## Critérios de Aceitação

### CA-01: Scaffolding Executável
```gherkin
Dado que o repositório foi clonado
Quando executo docker-compose up --build
Então os serviços api, db e redis iniciam sem erros
E a API responde em http://localhost:8000/health com status 200
E a documentação OpenAPI está disponível em /docs
```

### CA-02: Conectividade com Banco
```gherkin
Dado que o container db está rodando
Quando a aplicação inicia
Então executa as migrações Alembic automaticamente (ou via script)
E o endpoint /health retorna "database": "connected"
```

### CA-03: Segurança de Headers
```gherkin
Dado qualquer requisição para a API
Quando inspeciono os headers de resposta
Então vejo X-Content-Type-Options, X-Frame-Options, HSTS, CSP
E o rate limiting está ativo (rejeita após N requisições)
```

### CA-04: Testes Passando
```gherkin
Dado que o ambiente virtual está configurado
Quando executo pytest tests/
Então todos os testes unitários e de integração passam
E o coverage report mostra ≥ 80% para src/api/ e src/core/
```

## Dependências

### Pré-requisito
- **Spec 000** — consome os contratos de domínio (\`ArchitectureGraph\`, \`Threat\`, \`EnrichedThreat\`, \`Job\`) definidos em \`src/domain/models.py\`.

### Pré-requisito
- **Spec 000** — esta spec consome os contratos de domínio (`ArchitectureGraph`, `Threat`, `EnrichedThreat`, `Job`) definidos em `src/domain/models.py`.


### Internas (Specs que dependem desta)
- `003-component-detection-service` — precisa da API para receber uploads
- `004-stride-engine` — precisa da estrutura de models/services
- `005-vulnerability-contramedidas` — precisa da estrutura de models/services
- `006-report-generator` — precisa da estrutura de models/services
- `007-ci-cd-github-actions` — depende do scaffolding existente

### Bibliotecas Python
- `fastapi[standard]==0.115.x`
- `pydantic==2.x`
- `pydantic-settings==2.x`
- `sqlalchemy[asyncio]==2.0.x`
- `asyncpg==0.30.x`
- `alembic==1.14.x`
- `slowapi==0.1.x` (rate limiting)
- `python-multipart==0.0.x` (uploads)
- `httpx==0.28.x` (testes async)
- `pytest-asyncio==0.25.x`
- `orjson==3.10.x`

## Decisões Técnicas (ADR)

### ADR-001: FastAPI + Pydantic v2 + SQLAlchemy 2.0
- **Contexto**: Precisamos de uma API moderna, tipada, com documentação automática.
- **Decisão**: Usar FastAPI com Pydantic v2 e SQLAlchemy 2.0 (async).
- **Justificativa**: Stack já validada na Fase 4. Performance excelente. Suporte nativo a async. Documentação automática reduz trabalho manual.
- **Consequências**: Curva de aprendizado com SQLAlchemy 2.0 (novo estilo de mapeamento). Requer `asyncpg` para PostgreSQL async.

### ADR-002: PostgreSQL + Alembic
- **Contexto**: Precisamos persistir jobs de análise e relatórios.
- **Decisão**: PostgreSQL 17 com Alembic para migrações.
- **Justificativa**: Robustez, suporte a JSONB (para metadados flexíveis), ACID. Alembic é padrão da comunidade SQLAlchemy.
- **Consequências**: Adiciona complexidade de infraestrutura (container DB). SQLite não é suficiente para concorrência real.

### ADR-003: Rate Limiting via slowapi + Redis
- **Contexto**: OWASP API Top 10 exige proteção contra abuso.
- **Decisão**: `slowapi` com backend Redis.
- **Justificativa**: Integração simples com FastAPI. Redis já está no docker-compose para cache/fila futura.
- **Consequências**: Se Redis cair, o rate limiting pode falhar (fallback para in-memory configurável).

## Módulos Planejados

| Arquivo | Responsabilidade |
|---------|------------------|
| `src/api/main.py` | App FastAPI, lifespan, middlewares, inclusão de routers |
| `src/api/routes/health.py` | GET /health |
| `src/api/routes/threat_model.py` | Placeholder routes (POST, GET — implementado nas specs filhas) |
| `src/api/dependencies.py` | get_db(), get_settings(), get_storage() |
| `src/core/config.py` | Settings (Pydantic) |
| `src/core/security.py` | Rate limiter, security headers, CORS, magic bytes validation |
| `src/core/logging.py` | Configuração de logging JSON |
| `src/models/base.py` | DeclarativeBase |
| `src/models/job.py` | Modelo Job |
| `src/infrastructure/database.py` | Engine, SessionLocal, session manager |
| `src/infrastructure/storage.py` | LocalFileStorage (save, delete, get_path) |
| `tests/conftest.py` | Fixtures pytest |
| `tests/unit/test_health.py` | Testes do healthcheck |
| `tests/integration/test_api_base.py` | Testes de integração DB + upload |

---

*Spec reescrita em: 2026-06-21 (quebrada da monolítica 001 original)*
