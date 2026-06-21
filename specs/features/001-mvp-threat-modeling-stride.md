# Spec: MVP de Modelagem de Ameaças com IA (STRIDE)

---

## Contexto / Motivação

A FIAP Software Security precisa validar a viabilidade de uma nova funcionalidade: usar Inteligência Artificial para realizar automaticamente a modelagem de ameaças baseada na metodologia STRIDE, a partir de diagramas de arquitetura de software em imagem. O sistema deve identificar componentes (usuários, servidores, bases de dados, APIs, etc.), aplicar STRIDE, e gerar um relatório com vulnerabilidades e contramedidas.

## Objetivo

Desenvolver um MVP end-to-end que:
1. Receba uma imagem de diagrama de arquitetura de software.
2. Identifique automaticamente os componentes da arquitetura usando Visão Computacional + IA.
3. Aplique a metodologia STRIDE para cada componente identificado.
4. Gere um Relatório de Modelagem de Ameaças estruturado.
5. Busque vulnerabilidades conhecidas e contramedidas específicas para cada ameaça identificada.

## Requisitos Funcionais (RF)

### RF-01: Upload e Pré-processamento de Imagem
- O sistema deve aceitar upload de imagens (PNG, JPG, JPEG) contendo diagramas de arquitetura.
- Deve validar formato por magic bytes (herdado Fase 4).
- Deve pré-processar a imagem (redimensionamento, normalização, binarização se necessário) para melhorar a detecção.

### RF-02: Detecção de Componentes de Arquitetura (Computer Vision)
- O sistema deve identificar componentes em diagramas de arquitetura: usuários/clientes, servidores/web apps, APIs, bases de dados, filas/mensageria, caches, serviços externos, etc.
- Deve utilizar um modelo de Visão Computacional treinado com dataset anotado (detecção supervisionada).
- Cada componente detectado deve conter: tipo, bounding box, e confiança.

### RF-03: Análise de Relacionamentos entre Componentes
- A partir das posições dos componentes na imagem, inferir fluxos de dados (Data Flows) entre eles.
- Identificar trust boundaries (fronteiras de confiança) na arquitetura.

### RF-04: Modelagem de Ameaças STRIDE
- Para cada componente e fluxo de dados identificado, aplicar sistematicamente as 6 categorias STRIDE:
  - **S** - Spoofing (Autenticação)
  - **T** - Tampering (Integridade)
  - **R** - Repudiation (Não-repudiação)
  - **I** - Information Disclosure (Confidencialidade)
  - **D** - Denial of Service (Disponibilidade)
  - **E** - Elevation of Privilege (Autorização)
- Gerar uma matriz de ameaças por componente.

### RF-05: Busca de Vulnerabilidades e Contramedidas
- Para cada ameaça identificada, buscar vulnerabilidades conhecidas (CVE, CWE) relacionadas ao tipo de componente.
- Sugerir contramedidas específicas para cada ameaça (ex: MFA para Spoofing, TLS para Information Disclosure, Rate Limiting para DoS).

### RF-06: Geração de Relatório
- Gerar um relatório estruturado (JSON e Markdown/HTML) contendo:
  - Componentes identificados
  - Fluxos de dados mapeados
  - Ameaças STRIDE por componente
  - Vulnerabilidades associadas
  - Contramedidas recomendadas
  - Score de risco (opcional: DREAD)

### RF-07: API REST
- Expor endpoints FastAPI para:
  - `POST /api/v1/threat-model/analyze` — Upload de imagem + análise completa
  - `GET /api/v1/threat-model/{id}` — Consultar resultado
  - `GET /api/v1/threat-model/{id}/report` — Baixar relatório (Markdown/PDF)
  - `GET /health` — Healthcheck

## Requisitos Não-Funcionais (RNF)

### RNF-01: Performance
- Tempo de resposta para análise de imagem: < 30 segundos (GPU) ou < 2 minutos (CPU).
- Suportar processamento assíncrono para imagens grandes.

### RNF-02: Segurança
- OWASP API Top 10 compliance (herdado Fase 4).
- Rate limiting em todos os endpoints.
- Headers de segurança (CSP, HSTS, X-Content-Type-Options).
- Não logar imagens ou dados sensíveis da arquitetura.

### RNF-03: Escalabilidade
- Containerização com Docker + Docker Compose.
- Suporte a workers assíncronos (Celery/RQ) para processamento de imagens.

### RNF-04: Qualidade de Código
- Testes unitários (pytest) com > 80% coverage.
- Lint/format (ruff/black).
- Type hints obrigatórios.
- Documentação OpenAPI automática (FastAPI).

### RNF-05: Dataset e Treinamento
- Dataset deve ser versionado (DVC ou similar) ou documentado.
- Anotações no formato COCO ou YOLO.
- Notebook de treinamento reproduzível.

## Critérios de Aceitação

### CA-01: Upload e Validação
```gherkin
Dado que o usuário envia uma imagem PNG de diagrama de arquitetura
Quando faz POST para /api/v1/threat-model/analyze com a imagem
Então o sistema valida o formato, pré-processa e retorna um job ID
```

### CA-02: Detecção de Componentes
```gherkin
Dado que o job de análise está em execução
Quando o modelo de CV processa a imagem
Então identifica pelo menos 80% dos componentes esperados nas arquiteturas de teste
E retorna tipos: usuário, web_server, api, database, queue, external_service, etc.
```

### CA-03: Análise STRIDE
```gherkin
Dado que os componentes foram detectados
Quando o módulo STRIDE é aplicado
Então gera ameaças para cada categoria (S, T, R, I, D, E) por componente/fluxo
E prioriza as ameaças mais críticas
```

### CA-04: Relatório Completo
```gherkin
Dado que a análise STRIDE foi concluída
Quando o usuário consulta GET /api/v1/threat-model/{id}/report
Então recebe um relatório contendo todos os componentes, ameaças, vulnerabilidades e contramedidas
```

### CA-05: Arquiteturas de Teste
```gherkin
Dado as arquiteturas de teste fornecidas pelo avaliador
Quando o sistema processa ambas as imagens
Então identifica corretamente os componentes principais
E gera ameaças STRIDE relevantes para cada arquitetura
```

## Dependências

### Serviços Externos
- **NVD (National Vulnerability Database)** — para busca de CVEs (opcional, pode ser cache local).
- **OWASP Cheat Sheet Series** — para contramedidas (pode ser embeddado localmente).

### Bibliotecas Python
- `fastapi` + `uvicorn` — API REST
- `pydantic` v2 — Validação de dados
- `sqlalchemy` 2.0 + `alembic` — Persistência de relatórios
- `opencv-python` + `pillow` — Pré-processamento de imagens
- `torch` + `torchvision` — Framework de treinamento/detecção
- `ultralytics` (YOLOv8) — Modelo base de detecção de objetos
- `pytest` + `httpx` — Testes
- `ruff` + `black` + `mypy` — Qualidade de código

### Infraestrutura
- PostgreSQL — Banco de dados de relatórios
- Redis — Cache e fila de jobs (opcional)
- MinIO/S3 — Armazenamento de imagens (opcional, pode ser filesystem)

## Decisões Técnicas (ADR)

### ADR-001: Framework de Detecção — YOLOv8
- **Contexto**: Precisamos detectar componentes de arquitetura em imagens.
- **Decisão**: Usar YOLOv8 (Ultralytics) como backbone de detecção.
- **Justificativa**:
  - Já utilizado na Fase 4 (familiaridade com a equipe).
  - Excelente velocidade/qualidade para detecção de objetos.
  - Fácil fine-tuning com dataset customizado.
  - Suporte a exportação para ONNX/TensorRT.
- **Consequências**: Dataset precisa ser anotado no formato YOLO (txt). Notebook de treinamento deve usar `ultralytics`.

### ADR-002: Metodologia STRIDE — Implementação Programática
- **Contexto**: Aplicar STRIDE automaticamente sobre componentes detectados.
- **Decisão**: Criar um módulo Python que mapeia tipos de componentes para ameaças STRIDE pré-definidas, com extensão para busca dinâmica de CVEs.
- **Justificativa**:
  - STRIDE é uma metodologia bem estabelecida com mapeamentos conhecidos por tipo de componente.
  - Permite automação sem depender de LLM externo (mas pode ser complementado).
  - CVEs adicionam dinamismo e atualidade às ameaças.
- **Consequências**: Manter uma base de conhecimento (knowledge base) de ameaças por componente. Atualizar periodicamente.

### ADR-003: Arquitetura do Sistema — API + Workers Assíncronos
- **Contexto**: Processamento de imagens pode ser demorado.
- **Decisão**: FastAPI expõe endpoints síncronos para healthcheck e assíncronos para análise. Workers processam jobs em background.
- **Justificativa**:
  - FastAPI + Pydantic v2 já utilizado na Fase 4.
  - Workers evitam timeout em uploads grandes.
  - Fácil escalar horizontalmente.
- **Consequências**: Adicionar complexidade com fila (Redis/Celery). API precisa expor status de job.

## Módulos Planejados (Referência para Implementação)

| Módulo | Arquivo(s) Planejados |
|--------|------------------------|
| Upload/Pré-processamento | `src/api/routes/upload.py`, `src/services/image_preprocessor.py` |
| Detecção de Componentes | `src/services/object_detector.py`, `src/infrastructure/ml/yolo_model.py` |
| Análise de Relacionamentos | `src/services/relationship_analyzer.py` |
| STRIDE Engine | `src/services/stride_engine.py`, `src/core/stride_mappings.py` |
| Vulnerabilidades | `src/services/vulnerability_lookup.py`, `src/infrastructure/cve_client.py` |
| Relatórios | `src/services/report_generator.py`, `src/core/templates/stride_report.md` |
| API | `src/api/main.py`, `src/api/routes/threat_model.py` |
| Models | `src/models/job.py`, `src/models/report.py` |

## Entregáveis do Hackathon Relacionados

- [ ] Documentação detalhando o fluxo (coberto por este SDD + docs/)
- [ ] Vídeo de até 15 minutos explicando a solução
- [ ] Link do GitHub do projeto

---

*Spec criada em: 2026-06-21*
*Baseada em: Context7 (FastAPI, PyTorch, OpenCV) + STRIDE methodology*
