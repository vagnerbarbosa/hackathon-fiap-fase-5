# Spec: CI/CD com GitHub Actions

---

## Contexto / Motivação

O hackathon exige entregar um projeto funcional no GitHub. Um pipeline de CI/CD garante que o código esteja sempre testado, formatado, e pronto para execução. Esta spec foca na configuração do GitHub Actions para automação de qualidade.

## Objetivo

Configurar um pipeline GitHub Actions que:
1. Execute lint e formatação em todo PR/push.
2. Rode testes unitários e de integração.
3. Verifique coverage mínimo: 70%.
4. Build e push de imagem Docker (opcional, mas recomendado).
5. Valide a estrutura do dataset e modelo.

## Requisitos Funcionais (RF)

### RF-01: Workflow de CI — Pull Requests
Arquivo `.github/workflows/ci.yml`:

**Triggers**: `push` para `main`, `pull_request` para `main`

**Jobs**:

1. **lint**:
   - Instalar dependências via Poetry
   - `ruff check src/`
   - `ruff format --check src/`
   - `mypy src/`
   - Falhar se houver erro de lint ou formatação

2. **test**:
   - Rodar PostgreSQL e Redis via `services` do GitHub Actions
   - `pytest tests/ --cov=src --cov-report=xml --cov-fail-under=70`
   - Upload de coverage para Codecov (opcional)

3. **dataset-validation**:
   - Verificar se `dataset/data.yaml` existe e está válido
   - Verificar se `dataset/train/images/` tem ≥ 70 imagens
   - Verificar se `dataset/val/images/` tem ≥ 20 imagens
   - Verificar se modelo `models/best.pt` existe (após treinamento)

4. **docker-build** (opcional):
   - Build da imagem Docker
   - Verificar se `docker-compose up --build` sobe sem erros
   - Verificar se `/health` responde

### RF-02: Workflow de Release — Tags
Arquivo `.github/workflows/release.yml`:

**Triggers**: `push` de tags `v*` (ex: `v0.1.0`)

**Jobs**:
- Build da imagem Docker
- Push para DockerHub ou GitHub Container Registry (`ghcr.io`)
- Criar GitHub Release com notas automáticas

### RF-03: Proteção de Branch
Configurar no GitHub:
- `main` protegida: exige PR + review + CI passando antes de merge.
- Não permitir push direto para `main`.

## Requisitos Não-Funcionais (RNF)

### RNF-01: Performance
- Pipeline CI deve completar em < 5 minutos (sem Docker build) ou < 10 minutos (com Docker build).

### RNF-02: Custo
- Usar runners públicos do GitHub (free para repos públicos).
- Se repo privado, limitar jobs paralelos.

## Critérios de Aceitação

### CA-01: CI Passando
```gherkin
Dado um Pull Request aberto
Quando o GitHub Actions executa
Então todos os jobs (lint, test, dataset-validation) passam
E o PR pode ser mergeado
```

### CA-02: Proteção de Branch
```gherkin
Dado que a branch main está protegida
Quando tento fazer push direto para main
Então o GitHub rejeita
```

## Dependências

### Internas
- **Spec 001** — depende do scaffolding (pyproject.toml, tests/, Dockerfile)
- **Spec 002** — depende do dataset e modelo existirem

### Bibliotecas Python (dev)
- `pytest-cov==5.x`
- `ruff==0.4.x`
- `mypy==1.10.x`

## Decisões Técnicas (ADR)

### ADR-001: GitHub Actions vs. Alternativas
- **Contexto**: Poderíamos usar GitLab CI, Jenkins, ou Azure DevOps.
- **Decisão**: GitHub Actions (nativo do GitHub).
- **Justificativa**: Repositório já está no GitHub. Integração perfeita. Runners gratuitos. O hackathon pede link do GitHub.
- **Consequências**: Nenhuma — melhor escolha para o contexto.

### ADR-002: Lint como Gate de Segurança (Ruff + mypy)
- **Contexto**: Em projetos de segurança de software, código mal formatado ou sem tipagem pode esconder vulnerabilidades.
- **Decisão**: Ruff + mypy são **gates obrigatórios** no CI. Falha = merge bloqueado.
- **Justificativa**:
  - Ruff detecta padrões inseguros (ex: ,  com shell=True, imports circulares).
  - mypy previne erros de tipo que podem causar comportamento inesperado (DoS, Info Disclosure).
  - Ambos são rápidos (< 10s no CI) e têm zero custo de manutenção.
- **Consequências**: Desenvolvedores precisam configurar pre-commit hooks locais para evitar surpresas no CI.

### ADR-003: Cobertura Mínima de Testes — 70%
- **Contexto**: Cobertura 100% é idealista para um MVP de hackathon; 0% é inaceitável para segurança.
- **Decisão**: 70% de cobertura mínima como gate de CI.
- **Justificativa**:
  - 70% cobre os caminhos críticos (upload, detecção, STRIDE, relatório) sem exigir testes triviais.
  - Foco em testes de integração para os serviços de segurança (STRIDE, vulnerabilidades).
  - Permite evolução rápida sem sacrificar confiança.
- **Consequências**: Módulos de UI/templates podem ter cobertura menor; lógica de segurança deve ter > 90%.

## Módulos Planejados

| Arquivo | Responsabilidade |
|---------|------------------|
| `.github/workflows/ci.yml` | Lint, testes, validação de dataset, Docker build |
| `.github/workflows/release.yml` | Build e push de imagem em tags |
| `scripts/run_ci_checks.sh` | Script local para rodar os mesmos checks do CI |

---

*Spec criada em: 2026-06-21*
