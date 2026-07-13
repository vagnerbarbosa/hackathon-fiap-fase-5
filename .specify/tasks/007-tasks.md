# Tasks: CI/CD com GitHub Actions (Spec 007)

**Feature**: 007-ci-cd-github-actions | **Branch**: `feature/007-ci-cd`

---

## Phase 1: Workflow de CI — Pull Requests

Configurar o pipeline de integração contínua para lint, testes e validação.

- [x] T001 Substituir placeholder `.github/workflows/ci.yml` pelo workflow completo
  - Job `lint`: ruff check, ruff format --check, mypy
  - Job `test`: serviços PostgreSQL + Redis, pytest com coverage ≥ 70%, upload de artefato XML
  - Job `dataset-validation`: verificar data.yaml, imagens de train (≥70), val (≥20), models/best.pt
  - Job `docker-build`: build + health check de `/health` (apenas em push para main)

---

## Phase 2: Workflow de Release — Tags

Configurar o pipeline de release automático em tags semânticas.

- [x] T002 Criar `.github/workflows/release.yml`
  - Job `docker-publish`: build + push para GHCR com tags semver, SLSA provenance, SBOM
  - Job `smoke-test`: pull da imagem publicada, /health + /version check
  - Job `github-release`: criar GitHub Release com notas auto-geradas e comando docker pull
  - Suporte opcional a DockerHub via secrets `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN`

---

## Phase 3: Script de CI Local

Script para rodar os mesmos checks do CI localmente antes de fazer push.

- [x] T003 Criar `scripts/run_ci_checks.sh`
  - Suporte a flags: `--lint`, `--test`, `--dataset`, `--docker`, `--fix`, `--help`
  - Cores e relatório de resumo (pass/warn/fail counts)
  - Ativação automática do virtualenv Poetry
  - Sem flags: executa lint + format + types + tests + dataset (docker opcional)

---

## Phase 4: Proteção de Branch (Manual — GitHub UI)

Configurações a serem aplicadas manualmente no GitHub após merge da spec.

- [ ] T004 Configurar proteção de branch `main` no GitHub
  - Acessar: Settings → Branches → Branch protection rules → Add rule
  - Branch name pattern: `main`
  - Marcar: "Require a pull request before merging"
  - Marcar: "Require status checks to pass before merging"
    - Adicionar: `lint`, `test`, `dataset-validation`
  - Marcar: "Do not allow bypassing the above settings"
  - Salvar regra

---

## Task Summary

| Phase | Tasks | Status | Focus |
|-------|-------|--------|-------|
| Phase 1: CI Workflow | 1 | ✅ Completo | lint, test, dataset, docker |
| Phase 2: Release Workflow | 1 | ✅ Completo | GHCR push, release notes |
| Phase 3: Script Local | 1 | ✅ Completo | Paridade com CI |
| Phase 4: Branch Protection | 1 | ⏳ Manual | GitHub UI config |

**Total Tasks**: 4
**Automated**: 3
**Manual (GitHub UI)**: 1

---

## Módulos Criados

| Arquivo | Responsabilidade |
|---------|------------------|
| `.github/workflows/ci.yml` | Lint, testes, validação de dataset, Docker build |
| `.github/workflows/release.yml` | Build e push de imagem em tags `v*` |
| `scripts/run_ci_checks.sh` | Script local para rodar os mesmos checks do CI |

---

## Secrets Necessários

| Secret | Obrigatório | Descrição |
|--------|-------------|-----------|
| `GITHUB_TOKEN` | ✅ Automático | Criado pelo GitHub Actions automaticamente |
| `CODECOV_TOKEN` | ⚙ Opcional | Upload de coverage para Codecov |
| `DOCKERHUB_USERNAME` | ⚙ Opcional | Push adicional para DockerHub |
| `DOCKERHUB_TOKEN` | ⚙ Opcional | Token de acesso do DockerHub |

---

## Critérios de Aceitação Verificados

- [x] **CA-01**: Jobs `lint`, `test`, `dataset-validation` definidos e configurados corretamente
- [ ] **CA-02**: Proteção de branch `main` ativa (requer configuração manual no GitHub UI — T004)

---

*Tasks geradas: 2026-07-12*
*Spec: specs/features/007-ci-cd-github-actions.md*
