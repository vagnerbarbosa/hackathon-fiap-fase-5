# FIAP Tech Challenge — Fase 5 (Hackathon)

> ⚠️ **REGRA OBRIGATÓRIA — Context7**: Todo código gerado neste projeto **DEVE** consultar o MCP **Context7** para buscar as boas práticas, documentação e exemplos mais recentes de qualquer biblioteca, framework, SDK, API ou CLI utilizados. Isso inclui FastAPI, Pydantic, LangChain, PyTorch, Docker, Azure SDKs, entre outros. A regra aplica-se mesmo quando o conhecimento parece óbvio — os dados de treinamento podem estar desatualizados. Preferir Context7 ao invés de Web Search para documentação técnica.
>
> *Esta regra está implementada via `~/.claude/rules/context7.md` e é monitorada automaticamente pelo Claude Code.*

---

## Visão Geral

### Desafio do Hackathon FIAP Fase 5

**Tema**: Modelagem de ameaças utilizando IA (Threat Modeling com STRIDE)
**Empresa**: FIAP Software Security
**Fonte**: `IADT - Fase 5 - Hackaton.pdf`

**Contexto**: A empresa deseja usar IA para identificar e tratar vulnerabilidades em arquiteturas de sistemas automaticamente. O desafio é criar uma solução que:
1. Receba um diagrama de arquitetura de software em imagem.
2. Identifique componentes (usuários, servidores, bases de dados, APIs, etc.) via Visão Computacional.
3. Aplique a metodologia **STRIDE** para modelagem de ameaças.
4. Gere um relatório com vulnerabilidades conhecidas e contramedidas específicas.

**Metodologia STRIDE**:
- **S**poofing → Autenticação
- **T**ampering → Integridade
- **R**epudiation → Não-repudiação
- **I**nformation Disclosure → Confidencialidade
- **D**enial of Service → Disponibilidade
- **E**levation of Privilege → Autorização

---

### Evolução das Fases Anteriores

- **Fase 3** ([vagnerbarbosa/tech-challenge-fase-3](https://github.com/vagnerbarbosa/tech-challenge-fase-3)): Assistente virtual médico com NLP, RAG, LangChain/LangGraph, fine-tuning de LLMs (LLaMA/Falcon) e anonimização LGPD.
- **Fase 4** ([vagnerbarbosa/tech-challenge-fase-4](https://github.com/vagnerbarbosa/tech-challenge-fase-4)): Plataforma de análise de saúde da mulher com detecção precoce de riscos maternos e sinais de violência doméstica, utilizando FastAPI, Azure AI (Language, Speech, Content Safety), YOLOv8/OpenCV e conformidade LGPD/OWASP.

**Fase 5 (Atual)** herda as melhores práticas das fases anteriores e aplica-as no domínio de segurança de software com threat modeling automatizado.

---

## Principais Tecnologias e Padrões Herdados

| Domínio | Fase 3 | Fase 4 | Aplicar na Fase 5 |
|---------|--------|--------|-------------------|
| Backend | Python 3.10+, LangChain, LangGraph | Python 3.11+, FastAPI, Pydantic v2 | **Combinar**: FastAPI + Pydantic v2 + integração com orquestração de IA |
| IA/ML | LLaMA/Falcon fine-tuned, RAG, PEFT/LoRA | Azure AI, YOLOv8, OpenCV | **Avaliar**: usar modelo multimodal ou serviços cloud conforme necessidade do hackathon |
| Dados | SQLite, JSONL, TF-IDF/SentenceTransformers | Azure Blob, scrubbing PII | **Manter**: anonimização LGPD obrigatória; avaliar vector DB para RAG |
| DevOps | Docker, scripts de scraping | Docker Compose, OWASP headers, rate limiting | **Manter**: containerização, segurança de API, headers de segurança |
| Compliance | LGPD | LGPD + OWASP API Top 10 | **Expandir**: manter ambas as conformidades |

---

## Diretrizes de Arquitetura

### 1. Estrutura de Diretórios Sugerida

```
├── src/
│   ├── api/              # Rotas FastAPI, controllers, DTOs (Pydantic v2)
│   ├── core/             # Configurações, segurança, logging, middlewares
│   ├── services/         # Casos de uso e orquestração de domínio
│   ├── infrastructure/     # Adaptadores: DB, filas, clientes externos (Azure, OpenAI, etc.)
│   ├── models/           # Entidades de domínio (ORMs ou dataclasses)
│   └── workers/          # Tarefas assíncronas (se necessário)
├── tests/                # Testes unitários, integração e E2E
├── docs/                 # Documentação geral (exceto specs)
├── specs/                # Especificações SpeckIt / SDD
├── scripts/              # Scripts de setup, migração, seed
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml        # Poetry ou uv
└── CLAUDE.md             # Este arquivo
```

### 2. Princípios de Design

- **Clean Architecture / Ports and Adapters**: desacoplar domínio de frameworks e infraestrutura.
- **API First**: definir contratos OpenAPI antes de implementar endpoints.
- **Security by Default**: todas as rotas devem ter rate limiting, validação de entrada, e proteção contra injeção.
- **Privacy by Design**: dados sensíveis devem ser anonimizados ou pseudonimizados antes de logging/persistência (LGPD).
- **Observability**: logging estruturado, métricas expostas (health probes), e tracing quando possível.

---

## SpeckIt e SDD (Software Design Document)

Este projeto adota **SpeckIt** para gerenciamento de especificações e geração do SDD.

### Como usar SpeckIt neste projeto

1. **Toda feature nova** deve começar com uma especificação em `specs/features/<nome-da-feature>.md`.
2. **Formato mínimo da spec**:
   - Contexto / Motivação
   - Objetivo
   - Requisitos Funcionais (RF)
   - Requisitos Não-Funcionais (RNF)
   - Critérios de Aceitação (Given/When/Then ou checklist)
   - Dependências (serviços, models, APIs externas)
   - Decisões Técnicas (ADR leve)
3. **Consolidação**: antes de iniciar implementação, validar se a spec está completa. Use o SDD gerado como fonte da verdade para prompts de IA e reviews.
4. **Integração com código**: specs devem referenciar nomes de arquivos/módulos planejados para facilitar traceabilidade.

### Diretório de Specs

```
specs/
├── sdd.md                # Documento mestre (gerado/consolidado)
├── features/
│   └── .gitkeep
├── architecture/
│   └── .gitkeep
└── adrs/
    └── .gitkeep
```

---

## MCPs Configurados

Este projeto utiliza servidores MCP para ampliar o contexto e a produtividade:

### 1. Context7 MCP (Obrigatório — Boas Práticas de Código)

**Status**: ✅ Configurado e ativo

- **Servidor**: `https://mcp.context7.com/mcp`
- **Skill/Rule**: Instalada em `~/.claude/rules/context7.md` e `~/.claude/skills/context7-mcp/SKILL.md`
- **Propósito**: Buscar documentação atualizada, versões recentes e boas práticas de qualquer biblioteca, framework, SDK, API ou CLI tool. Isso garante que o código gerado sempre siga as convenções mais recentes.

**Como funciona automaticamente**:
- Sempre que o usuário (ou eu) perguntar sobre alguma biblioteca (ex: `FastAPI`, `LangChain`, `PyTorch`, `Docker`, `Kubernetes`, `React`, `Next.js`), o Context7 é acionado automaticamente para buscar a documentação mais recente.
- A rule instrui: *"Use even when you think you know the answer — your training data may not reflect recent changes."*

**Exemplos de uso para este projeto**:
- "Quais as melhores práticas do FastAPI 0.115+?"
- "Como configurar Pydantic v2 corretamente?"
- "Qual a sintaxe mais recente do LangChain para RAG?"
- "Docker compose healthcheck para PostgreSQL"

### 2. MCPs do GitHub

**Status**: ✅ `gh` autenticado e funcional

Utilizados para:
- Buscar issues e pull requests dos repositórios base (fase-3 e fase-4) como referência.
- Criar issues, comentários e pull requests durante o desenvolvimento.
- Ler código-fonte dos repos base para reutilização de padrões comprovados.

#### Repositórios Base

- `vagnerbarbosa/tech-challenge-fase-3`
- `vagnerbarbosa/tech-challenge-fase-4`

#### Boas Práticas com MCP GitHub

- Sempre buscar padrões similares nos repos base antes de reinventar soluções.
- Ao copiar/adaptar código, verificar licença (assumir MIT ou privado conforme contexto) e referenciar a origem em comentários.
- Usar issues para rastrear tarefas do hackathon e associar aos critérios de aceitação das specs.

---

## Stack Tecnológica Definida (Pós-Análise do Desafio)

| Camada | Tecnologia | Justificativa |
|--------|-----------|---------------|
| Linguagem | Python 3.11+ | Herdado Fase 3/4 |
| Web Framework | FastAPI + Pydantic v2 | API REST para upload e relatórios; herda segurança da Fase 4 |
| ORM / DB | SQLAlchemy 2.0 + PostgreSQL | Persistência de jobs e relatórios |
| Computer Vision | OpenCV + YOLOv8 (Ultralytics) | Detecção de componentes em diagramas; já usado na Fase 4 |
| Framework IA | PyTorch + torchvision | Treinamento supervisionado do modelo de detecção |
| Threat Modeling | Módulo Python customizado (STRIDE) | Mapeamento programático de ameaças por tipo de componente |
| Vulnerabilidades | NVD API / OWASP Cheat Sheets | Busca de CVEs e contramedidas |
| Container | Docker + Docker Compose | Entrega do MVP |
| Testes | pytest + httpx (async) | Herdado Fase 4 |
| Lint/Format | ruff, black, mypy | Qualidade de código |
| Gerenciamento de Dependências | Poetry | Herdado Fase 3/4 |

---

## Checklist de Início de Projeto

- [x] Definir tema/desafio exato do hackathon.
- [x] Criar specs no formato SpeckIt (`specs/features/`):
  - [x] `001-api-core-scaffolding.md` — Scaffolding FastAPI + Docker + segurança
  - [x] `002-dataset-training-yolo.md` — Dataset e treinamento YOLOv8
  - [x] `003-component-detection-service.md` — Detecção de componentes (CV)
  - [x] `004-stride-engine.md` — Motor de análise STRIDE
  - [x] `005-vulnerability-contramedidas.md` — Busca de CVEs/CWEs e contramedidas
  - [x] `006-report-generator.md` — Geração de relatórios Markdown/HTML
  - [x] `007-ci-cd-github-actions.md` — CI/CD com GitHub Actions
  - [x] `008-video-demo-script.md` — Roteiro do vídeo de 15 min
- [ ] Configurar GitHub Actions (CI básico: lint + testes).
- [x] Verificar conectividade com MCPs do GitHub.
- [x] Verificar conectividade com MCP **Context7** (obrigatório para todas as bibliotecas).
- [x] Escolher entre herdar scaffolding da Fase 3 ou Fase 4 (ou híbrido).
- [ ] Criar `docker-compose.yml` local.
- [ ] Gerar dataset sintético de diagramas de arquitetura.
- [ ] Anotar dataset no formato YOLO.
- [ ] Treinar modelo YOLOv8n para detecção de componentes.
- [ ] Implementar módulo STRIDE Engine.
- [ ] Implementar API FastAPI com endpoints de análise.
- [ ] Implementar geração de relatório Markdown/PDF.
- [ ] Rodar primeiro teste de integração (healthcheck).
- [ ] Testar com arquiteturas de teste do hackathon.

---

## LGPD e Segurança (Não-Negociável)

1. **Anonimização**: usar técnicas de Fase 3 + Fase 4 para remover/ mascarar PII antes de logs e treinamento.
2. **Headers HTTP**: CSP, HSTS, X-Content-Type-Options, X-Frame-Options.
3. **Rate Limiting**: implementar desde o primeiro endpoint.
4. **Validação de arquivos**: magic bytes para uploads (herdado Fase 4).
5. **Logs**: nunca logar tokens, senhas, CPF, ou dados clínicos identificáveis.

---

## Convenções de Código

- **Context7 é obrigatório**: ao escrever ou revisar qualquer código que dependa de bibliotecas/frameworks, consultar o MCP Context7 para garantir que estamos seguindo a documentação e as boas práticas mais recentes. Nunca assumir que o conhecimento prévio está atualizado.
- Idioma do código: **inglês** (nomes de variáveis, funções, classes).
- Idioma da documentação: **português** (docs, specs, comentários explicativos).
- Commits em português, imperativo, seguindo [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) (ex: `feat: adiciona endpoint de análise de risco`, `docs: atualiza README`, `fix: corrige validação de upload`).
- **Branching — regra obrigatória**: `main` é protegida. **NUNCA** commitar diretamente na `main`. Toda alteração passa por:
  1. Branch `feature/nome-da-spec` (ex: `feature/001-api-core-scaffolding`)
  2. Pull Request para `main`
  3. Review + CI passando antes de merge

---

## Links Úteis

- [Repositório Fase 3](https://github.com/vagnerbarbosa/tech-challenge-fase-3)
- [Repositório Fase 4](https://github.com/vagnerbarbosa/tech-challenge-fase-4)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [LGPD - Lei 13.709/2018](http://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)

---

*Última atualização: 2026-06-21*
