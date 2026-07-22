# Spec: CI/CD com GitHub Actions

---

## Contexto / Motivação

O hackathon exige entregar um projeto funcional no GitHub. Um pipeline de CI/CD garante que o código esteja sempre testado, formatado, e pronto para execução. Esta spec foca na configuração do GitHub Actions para automação de qualidade e versionamento semântico.

## Objetivo

Configurar um pipeline GitHub Actions que:
1. Execute lint e formatação em todo PR/push.
2. Rode testes unitários e de integração.
3. Verifique coverage mínimo: 70%.
4. Build e push de imagem Docker (opcional, mas recomendado).
5. Valide a estrutura do dataset e modelo.
6. **Gerencie versão do sistema automaticamente** (bump version + tags).

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

### RF-04: Versionamento Automatizado (NOVO)
Arquivo `.github/workflows/bump-version.yml`:

**Triggers**: `push` para `main` (após merge de PR)

**Jobs**:
1. **detect-changes**:
   - Verificar quais specs foram modificadas no commit
   - Determinar tipo de bump: major, minor, patch

2. **bump-version**:
   - Atualizar `src/core/config.py` → `app_version`
   - Atualizar `frontend/package.json` → `version` (opcional)
   - Commit com `[skip ci]` para evitar loop

3. **create-tag**:
   - Criar tag git no formato `v{major}.{minor}.{patch}`
   - Push tag para origin

**Regras de Bump**:
| Mudança | Exemplo | Versão |
|---------|---------|--------|
| Spec 000-009 nova | Feature completa | Minor (0.1.0 → 0.2.0) |
| Bug fix | Correção de segurança | Patch (0.2.0 → 0.2.1) |
| Breaking change | Altera contrato | Major (0.2.0 → 1.0.0) |

**Histórico de Versões (Tags)**:
| Tag | Descrição | Data |
|-----|-----------|------|
| `v0.0.1` | Setup Inicial do Projeto | 2026-06-21 |
| `v0.1.0` | Spec 000: Contratos de Domínio | 2026-07-09 |
| `v0.2.0` | Spec 001: API Core + Scaffolding | 2026-07-11 |
| `v0.3.0` | Spec 003: Component Detection (PR #11) | Pending |
| `v0.8.0` | Spec 008: Frontend React | Pending |

### RF-05: Sincronização de Versão API ↔ Frontend
**Implementado**:
- API define versão única em `src/core/config.py` → `app_version`
- Frontend busca versão via `GET /api/version`
- Ambos exibem a mesma versão no footer/console

**Exemplo**:
```json
// GET /api/version
{
  "name": "FIAP STRIDE API",
  "version": "0.2.0"
}
```

Frontend exibe: `v0.2.0` (quando disponível)

## Requisitos Não-Funcionais (RNF)

### RNF-01: Performance
- Pipeline CI deve completar em < 5 minutos (sem Docker build) ou < 10 minutos (com Docker build).

### RNF-02: Custo
- Usar runners públicos do GitHub (free para repos públicos).
- Se repo privado, limitar jobs paralelos.

### RNF-03: Versionamento
- Seguir SemVer (Semantic Versioning): `MAJOR.MINOR.PATCH`
- Tags sempre prefixadas com `v` (ex: `v0.2.0`)
- Changelog gerado automaticamente a partir de commits

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

### CA-03: Versionamento Automático
```gherkin
Dado que uma PR foi mergeada na main
Quando o workflow bump-version executa
Então a versão é incrementada automaticamente
E uma nova tag vX.X.X é criada
E ambos API e Frontend exibem a mesma versão
```

## Implementação

### Workflow de Bump Version (`.github/workflows/bump-version.yml`)

```yaml
name: Bump Version

on:
  push:
    branches: [main]

jobs:
  bump:
    runs-on: ubuntu-latest
    if: "!contains(github.event.head_commit.message, '[skip ci]')"
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Detect changes
        id: detect
        run: |
          # Verificar specs modificadas
          if git log -1 --pretty=format:%B | grep -q "Spec 00[0-9]"; then
            echo "bump=minor" >> $GITHUB_OUTPUT
          elif git log -1 --pretty=format:%B | grep -q "fix:"; then
            echo "bump=patch" >> $GITHUB_OUTPUT
          else
            echo "bump=patch" >> $GITHUB_OUTPUT
          fi
      
      - name: Bump version
        run: |
          # Extrair versão atual
          CURRENT_VERSION=$(grep 'app_version' src/core/config.py | grep -o '"[^"]*"' | tr -d '"')
          
          # Calcular nova versão (simplificado)
          IFS='.' read -r major minor patch <<< "$CURRENT_VERSION"
          
          if [ "${{ steps.detect.outputs.bump }}" == "minor" ]; then
            NEW_VERSION="$major.$((minor + 1)).0"
          else
            NEW_VERSION="$major.$minor.$((patch + 1))"
          fi
          
          # Atualizar config.py
          sed -i "s/app_version: str = Field(default=\"$CURRENT_VERSION\"/app_version: str = Field(default=\"$NEW_VERSION\"/" src/core/config.py
          
          # Commit e tag
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add src/core/config.py
          git commit -m "chore: bump version to $NEW_VERSION [skip ci]"
          git tag "v$NEW_VERSION"
          git push origin main --tags
```

## Dependências

### Pré-requisito
- **Spec 000** — consome os contratos de domínio (`ArchitectureGraph`, `Threat`, `EnrichedThreat`, `Job`) definidos em `src/domain/models.py`.

### Internas
- **Spec 001** — depende do scaffolding (pyproject.toml, tests/, Dockerfile)
- **Spec 002** — depende do dataset e modelo existirem
- **Spec 008** — frontend deve sincronizar versão com API

### Bibliotecas Python (dev)
- `pytest-cov==6.x`
- `ruff==0.9.x`
- `mypy==1.15.x`

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

### ADR-004: Versionamento Automatizado (NOVO)
- **Contexto**: Manter versões sincronizadas entre API e Frontend é trabalhoso manualmente.
- **Decisão**: Workflow GitHub Actions que detecta mudanças e incrementa versão automaticamente.
- **Justificativa**:
  - API é a fonte única da verdade para versão (`/api/version`)
  - Frontend busca versão da API dinamicamente
  - Tags são criadas automaticamente nos marcos
  - Histórico de versões rastreável (v0.0.1 → v0.1.0 → v0.2.0...)
- **Consequências**: Commits na main devem seguir conventional commits para detecção correta.

## Módulos Planejados

| Arquivo | Responsabilidade |
|---------|------------------|
| `.github/workflows/ci.yml` | Lint, testes, validação de dataset, Docker build |
| `.github/workflows/release.yml` | Build e push de imagem em tags |
| `.github/workflows/bump-version.yml` | Incrementa versão e cria tags automaticamente |
| `scripts/bash/run_ci_checks.sh` | Script local para rodar os mesmos checks do CI |

## Checklist de Implementação

- [ ] Workflow CI (ci.yml) funcional
- [ ] Workflow Release (release.yml) funcional
- [ ] Workflow Bump Version (bump-version.yml) funcional
- [ ] Branch `main` protegida no GitHub
- [ ] Tags históricas criadas (v0.0.1, v0.1.0, v0.2.0...)
- [ ] API e Frontend sincronizados na mesma versão
- [ ] Pre-commit hooks configurados localmente

---

*Spec atualizada em: 2026-07-11*
*Versão atual do sistema: v0.2.0*
*Próximas versões: v0.3.0 (Spec 003), v0.8.0 (Spec 008)*
