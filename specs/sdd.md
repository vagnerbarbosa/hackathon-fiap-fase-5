# Software Design Document (SDD) — Hackathon FIAP Fase 5

## Modelagem de Ameaças com IA (STRIDE)

---

## 1. Visão Geral do Projeto

### 1.1 Contexto
A FIAP Software Security deseja validar a viabilidade de uma nova funcionalidade: usar Inteligência Artificial para realizar automaticamente a modelagem de ameaças baseada na metodologia **STRIDE**, a partir de diagramas de arquitetura de software em imagem.

### 1.2 Metodologia STRIDE

| Letra | Ameaça | Propriedade Violada |
|-------|--------|---------------------|
| **S** | Spoofing | Autenticação |
| **T** | Tampering | Integridade |
| **R** | Repudiation | Não-repudiação |
| **I** | Information Disclosure | Confidencialidade |
| **D** | Denial of Service | Disponibilidade |
| **E** | Elevation of Privilege | Autorização |

### 1.3 Pipeline da Solução

```
Imagem de Arquitetura
        |
        v
[Pré-processamento + Upload]  --> Spec 001 (API Core)
        |
        v
[Detecção de Componentes]   --> Spec 002 (Dataset) + Spec 003 (CV)
        |
        v
[Análise STRIDE]              --> Spec 004 (Motor STRIDE)
        |
        v
[Busca de Vulnerabilidades]   --> Spec 005 (CVEs/CWEs)
        |
        v
[Geração de Relatório]        --> Spec 006 (Report)
        |
        v
  Relatório Markdown/HTML/JSON
```

---

## 2. Especificações (Specs SpeckIt)

Todas as specs estão em `specs/features/`:

| # | Arquivo | Título | Responsabilidade |
|---|---------|--------|------------------|
| 000 | `000-domain-contracts.md` | Contratos de Domínio | Models Pydantic v2 compartilhados (pré-requisito para todas) |
| 001 | `001-api-core-scaffolding.md` | API Core + Scaffolding | FastAPI, Pydantic v2, PostgreSQL, Docker, segurança OWASP |
| 002 | `002-dataset-training-yolo.md` | Dataset e Treinamento YOLO | Geração/ anotação de dataset, treino de modelo |
| 003 | `003-component-detection-service.md` | Serviço de Detecção de Componentes | Inferência YOLO, pré-processamento, heurística espacial |
| 004 | `004-stride-engine.md` | Motor STRIDE | Aplicação sistemática das 6 categorias STRIDE |
| 005 | `005-vulnerability-contramedidas.md` | Vulnerabilidades e Contramedidas | Busca de CVEs/CWEs, contramedidas OWASP |
| 006 | `006-report-generator.md` | Gerador de Relatórios | Templates Jinja2, Markdown/HTML/JSON |
| 007 | `007-ci-cd-github-actions.md` | CI/CD | GitHub Actions, lint, testes, Docker build |
| 008 | `008-video-demo-script.md` | Roteiro do Vídeo | Estrutura do vídeo de 15 min |

---

## 3. Arquitetura do Sistema

### 3.1 Diagrama de Componentes

```
+------------------+       +------------------+
|     Client       |       |   Admin/DEV      |
| (curl/frontend)  |       | (monitoramento)  |
+--------+---------+       +--------+---------+
         |                          |
         v                          v
+--------------------------------------------------------+
|                    FastAPI API (Port 8000)             |
|  +----------------+  +----------------+  +--------+  |
|  | Upload Route   |  | Report Route   |  | Health |  |
|  | (RF-01)        |  | (RF-06)        |  | Check  |  |
|  +--------+-------+  +--------+-------+  +--------+  |
|           |                 |                        |
|  +--------v-------+  +--------v-------+                |
|  | Component      |  | Report         |                |
|  | Detection      |  | Generator      |                |
|  | Service        |  | (Jinja2)       |                |
|  | (Spec 003)     |  | (Spec 006)     |                |
|  +--------+-------+  +--------+-------+                |
|           |                 |                        |
|  +--------v-------+  +--------v-------+                |
|  | STRIDE Engine  |  | Vulnerability  |                |
|  | (Spec 004)     |  | Service        |                |
|  +--------+-------+  | (Spec 005)     |                |
|           |          +--------+-------+                |
|           |                 |                          |
+--------------------------------------------------------+
            |                 |
            v                 v
+-----------+----+    +-----+--------+
|  PostgreSQL    |    |    Redis     |
|  (Jobs,        |    |  (Cache,     |
|   Reports)     |    |   Rate Limit)|
+----------------+    +--------------+
```

### 3.2 Fluxo de Dados (End-to-End)

1. **Upload** (`POST /api/v1/threat-model/analyze`)
   - Cliente envia imagem PNG/JPG.
   - API valida magic bytes, salva em storage, cria `Job` no PostgreSQL (status: `pending`).

2. **Processamento** (background ou sync)
   - `ComponentDetectionService` carrega imagem, pré-processa, executa YOLOv11n.
   - Retorna `ArchitectureGraph` (componentes + fluxos + trust boundaries).

3. **Análise STRIDE**
   - `StrideEngine` consome `ArchitectureGraph`.
   - Aplica mapeamento YAML por componente + categoria STRIDE.
   - Retorna `list[Threat]`.

4. **Enriquecimento**
   - `VulnerabilityService` consome `list[Threat]`.
   - Busca CWEs e contramedidas na base local (cache Redis).
   - Opcionalmente consulta NVD API.
   - Retorna `list[EnrichedThreat]`.

5. **Relatório**
   - `ReportGenerator` consome `EnrichedThreat` + `ArchitectureGraph`.
   - Renderiza templates Jinja2 → Markdown + JSON.
   - Salva em `reports/{job_id}.{md,json}`.
   - Atualiza `Job.output_report_path` e status: `completed`.

6. **Consulta**
   - Cliente faz `GET /api/v1/threat-model/{id}/report?format=md|json`.
   - API lê arquivo gerado e retorna.

---

## 4. Decisões Arquiteturais (ADRs Consolidadas)

| ID | Título | Decisão | Justificativa |
|----|--------|---------|---------------|
| ADR-001 | Framework CV | YOLOv11n (Ultralytics) | Velocidade, familiaridade Fase 4 (v8), fácil fine-tuning |
| ADR-002 | STRIDE Engine | Regras YAML puras Python | Determinístico, rápido, sem dependência de LLM externo |
| ADR-003 | API + Workers | FastAPI + Redis | Performance, escalabilidade, não bloqueia uploads |
| ADR-004 | ONNX Runtime | Prioridade ONNX em produção | ~2x speedup vs PyTorch, menor memória |
| ADR-005 | Base Local Vuln. | YAML como fonte primária | Funciona 100% offline, NVD é aprimoramento |
| ADR-006 | Relatórios | Markdown primário, HTML/PDF secundário | Universal, versionável, sem deps pesadas |
| ADR-007 | Dataset | Sintético + Real | Controle de variabilidade, acelera MVP |
| ADR-008 | Heurística de Relacionamentos | Proximidade espacial | Anotar setas é trabalhoso; heurística cobre 80% |

---

## 5. Dependências entre Specs

```
000 (Domain Contracts) ← pré-requisito de TODAS
  |
  +---> 001 (API Core)
  |       |
  |       +---> 003 (Component Detection)  --depends-on--> 002 (Dataset/Model)
  |       |         |
  |       |         v
  |       +---> 004 (STRIDE Engine)
  |       |         |
  |       |         v
  |       +---> 005 (Vulnerability Lookup)
  |       |         |
  |       |         v
  |       +---> 006 (Report Generator)
  |       |
  |       +---> 007 (CI/CD) --depends-on--> 001, 002
  |
  +---> 002 (Dataset) --produz--> modelos para 003

008 (Video) --depends-on--> 001-006 (sistema funcional)
```

---

## 6. Stack Tecnológica

| Camada | Tecnologia | Versão Sugerida |
|--------|-----------|-----------------|
| Linguagem | Python | 3.11+ |
| Web Framework | FastAPI | 0.115.x |
| Validação | Pydantic v2 | 2.x |
| ORM | SQLAlchemy | 2.0.x |
| DB Driver | asyncpg | 0.30.x |
| Migrations | Alembic | 1.14.x |
| Cache / Queue | Redis | 8.x |
| Computer Vision | OpenCV + YOLOv11 (Ultralytics) | 4.13.x / 8.3.x |
| Deep Learning | PyTorch + torchvision | 2.11.x |
| Templating | Jinja2 | 3.1.x |
| Testing | pytest + httpx | 8.x / 0.28.x |
| Lint | ruff + black + mypy | 0.9.x / 1.15.x |
| Container | Docker + Docker Compose | — |
| CI/CD | GitHub Actions | — |

---

## 7. Critérios de Sucesso do MVP

| Critério | Métrica |
|----------|---------|
| Componentes detectados | >= 80% nas arquiteturas de teste |
| mAP@0.5 do modelo | >= 0.75 |
| Cobertura STRIDE | Todas as 6 categorias aplicadas por componente relevante |
| Relatório gerado | Markdown + JSON completo com ameaças, vulnerabilidades e contramedidas |
| API funcional | Healthcheck < 100ms; upload e download funcionando |
| Testes | >= 80% coverage; todos passando |
| Docker | `docker-compose up --build` sobe sem erros |

---

## 8. Entregáveis do Hackathon

| Entregável | Status | Responsável |
|------------|--------|-------------|
| Documentação do fluxo | Em progresso (este SDD + specs) | Equipe |
| Vídeo de até 15 min | Planejado (Spec 008) | Equipe |
| Link do GitHub | Pendente criação do repo | Equipe |

---

*SDD consolidado em: 2026-06-21*
*Baseado em: Context7 (FastAPI, PyTorch, OpenCV, STRIDE) + requisitos do PDF do hackathon*
