# 📊 Relatório de Análise de Cobertura de Testes

**Data da Análise:** 2026-07-25  
**Executor:** Claude Code  
**Versão do Projeto:** 0.3.0

---

## 🎯 Resumo Executivo

| Métrica | Valor | Status |
|---------|-------|--------|
| **Cobertura Total** | **79.93%** | ✅ **CI ATENDIDO** |
| **Requisito CI** | ≥70% | ✅ ATENDIDO |
| **Requisito CLAUDE.md** | ≥80% | ⚠️ 0.07% abaixo do ideal |
| **Testes Passando** | **279 / 279 (100%)** | ✅ |
| **Testes Pulados** | 1 | - |

> **✅ STATUS:** Todos os gates de qualidade (ruff, mypy, pytest, cobertura ≥70%) estão passando. A cobertura está no limiar do objetivo ideal de 80% estabelecido no CLAUDE.md.

---

## 📋 Regras Estabelecidas no Projeto

### pyproject.toml
```toml
[tool.pytest.ini_options]
addopts = "--cov=src --cov-report=term-missing --cov-fail-under=60"
```

### CI/CD (.github/workflows/ci.yml)
```yaml
- name: Run tests with coverage
  run: >
    poetry run pytest tests/
    --cov=src
    --cov-report=xml
    --cov-report=term-missing
    --cov-fail-under=70
```

### CLAUDE.md (Documentação do Projeto)
> "CI gates: ruff + mypy + **70% test coverage** must pass before any PR can be merged."  
> "Critérios de Sucesso do MVP: Testes: **>= 80% coverage**; todos passando"

---

## 🔍 Análise Detalhada por Camada

### 1. Domain Layer (Modelos) ✅ EXCELENTE

| Arquivo | Stmts | Miss | Cover | Status |
|---------|-------|------|-------|--------|
| `src/domain/__init__.py` | 0 | 0 | 100% | ✅ |
| `src/domain/models.py` | 75 | 0 | **100%** | ✅ |

**Análise:** Modelos Pydantic v2 têm cobertura total.

---

### 2. API Layer ⚠️ PARCIAL

| Arquivo | Stmts | Miss | Cover | Status |
|---------|-------|------|-------|--------|
| `src/api/dependencies.py` | 27 | 0 | **100%** | ✅ |
| `src/api/main.py` | 30 | 8 | 73% | ⚠️ |
| `src/api/routes/health.py` | 26 | 2 | 92% | ✅ |
| `src/api/routes/threat_model.py` | **186** | **84** | **55%** | ⚠️ |

**Análise:**
- `threat_model.py` subiu de 18% para 55% após adição da classe `TestThreatModelPipeline` com 5 testes de integração do pipeline end-to-end.
- Pontas não cobertas: fallback de modelo não carregado, formatações de relatório secundárias e tratamentos de erro de I/O.

---

### 3. Core Layer ✅ BOM

| Arquivo | Stmts | Miss | Cover | Status |
|---------|-------|------|-------|--------|
| `src/core/circuit_breaker.py` | 89 | 3 | **97%** | ✅ |
| `src/core/config.py` | 33 | 6 | 82% | ✅ |
| `src/core/logging.py` | 35 | 21 | 40% | 🔴 |
| `src/core/retry.py` | 58 | 2 | **97%** | ✅ |
| `src/core/security.py` | 78 | 18 | 77% | ⚠️ |
| `src/core/stride_mappings.py` | 67 | 4 | **94%** | ✅ |
| `src/core/stride_rules.py` | 22 | 2 | **91%** | ✅ |
| `src/core/vulnerability_db.py` | 100 | 17 | 83% | ✅ |

**Análise:**
- Circuit breaker, retry, STRIDE e vulnerability_db com excelente cobertura.
- `logging.py` permanece em 40% por ser configuração estruturada de logs — impacto baixo para o pipeline.

---

### 4. Infrastructure Layer ⚠️ MISTO

| Arquivo | Stmts | Miss | Cover | Status |
|---------|-------|------|-------|--------|
| `src/infrastructure/cache/__init__.py` | 6 | 0 | **100%** | ✅ |
| `src/infrastructure/cache/cache_factory.py` | 24 | 0 | **100%** | ✅ |
| `src/infrastructure/cache/cache_interface.py` | 19 | 5 | 74% | ⚠️ |
| `src/infrastructure/cache/detection_cache.py` | 22 | 9 | 59% | ⚠️ |
| `src/infrastructure/cache/in_memory_cache.py` | 55 | 1 | **98%** | ✅ |
| `src/infrastructure/cache/redis_cache.py` | 77 | 37 | 52% | 🔴 |
| `src/infrastructure/database.py` | 53 | 8 | 85% | ✅ |
| `src/infrastructure/ml/__init__.py` | 2 | 0 | **100%** | ✅ |
| `src/infrastructure/ml/yolo_model.py` | 155 | 91 | 41% | 🔴 |
| `src/infrastructure/ml/yolo_stub.py` | 59 | 59 | **0%** | 🔴 |
| `src/infrastructure/repositories/job_repository.py` | 38 | 1 | **97%** | ✅ |
| `src/infrastructure/storage.py` | 38 | 4 | 89% | ✅ |

**Análise:**
- Cache in-memory e factory com cobertura excelente.
- Redis cache e YOLO model ficam abaixo de 50% por dependerem de serviços externos (Redis/ONNX) — aceitáveis para o MVP.
- `database.py` subiu para 85% com testes de conexão e fixtures de override de configuração.

---

### 5. Services Layer ⚠️ MISTO

| Arquivo | Stmts | Miss | Cover | Status |
|---------|-------|------|-------|--------|
| `src/services/__init__.py` | 15 | 0 | **100%** | ✅ |
| `src/services/component_detection.py` | 139 | 8 | **94%** | ✅ |
| `src/services/component_detector.py` | 71 | 20 | 72% | ✅ |
| `src/services/countermeasure_lookup.py` | 12 | 0 | **100%** | ✅ |
| `src/services/cve_lookup.py` | 53 | 3 | **94%** | ✅ |
| `src/services/csv_exporter.py` | 40 | 5 | 88% | ✅ |
| `src/services/image_preprocessor.py` | 84 | 13 | 85% | ✅ |
| `src/services/pdf_exporter.py` | 26 | 7 | 73% | ⚠️ |
| `src/services/relationship_analyzer.py` | 109 | 20 | 82% | ✅ |
| `src/services/report_generator.py` | 186 | 1 | **99%** | ✅ |
| `src/services/stride_engine.py` | 81 | 2 | **98%** | ✅ |
| `src/services/vulnerability_service.py` | 129 | 10 | 92% | ✅ |

**Análise:**
- Vulnerability service, CVE lookup e CSV exporter tiveram cobertura drasticamente ampliada após correção dos mocks de cache.
- Report generator e STRIDE engine próximos de 100%.

---

## 🔴 Arquivos com Cobertura Crítica (< 50%)

| Arquivo | Cobertura | Impacto | Ação Recomendada |
|---------|-----------|---------|------------------|
| `src/infrastructure/ml/yolo_model.py` | **41%** | 🟡 Médio | Testes com ONNX mockado (diferido para iteração futura) |
| `src/infrastructure/ml/yolo_stub.py` | **0%** | 🟢 Baixo | Stub de desenvolvimento; não crítico para CI |
| `src/core/logging.py` | **40%** | 🟢 Baixo | Configuração de logging estruturado; impacto operacional baixo |

> **Nota:** Não há mais arquivos da API ou dos serviços de negócio abaixo de 50%.

---

## ✅ Falhas de Testes

**Nenhuma falha.** Todos os testes do backend e do frontend estão passando:

- Backend: `279 passed, 1 skipped`
- Frontend: `48 passed`

---

## 🎯 Recomendações

### 🟢 Melhorias Contínuas

1. **Alcançar 80% de cobertura**
   - Cobertura atual: 79.93%
   - Adicionar testes pontuais em `src/api/routes/threat_model.py` (tratamento de modelo ausente) e `src/core/logging.py`.

2. **Testes end-to-end**
   - Diretório `tests/e2e/` reservado; adicionar suite mínima de upload → relatório quando o Docker estiver estável.

3. **Infraestrutura externa**
   - Cobertura do Redis e ONNX runtime requerem mocks mais elaborados ou serviços de teste em container.

---

## ✅ Checklist de Conformidade

| Requisito | Local | Valor | Atual | Status |
|-----------|-------|-------|-------|--------|
| Cobertura mínima | pyproject.toml | 60% | 79.93% | ✅ Superado |
| Cobertura CI | ci.yml | 70% | 79.93% | ✅ Atendido |
| Cobertura ideal | CLAUDE.md | 80% | 79.93% | ⚠️ Próximo |
| Testes passando | CLAUDE.md | 100% | 100% | ✅ Atendido |

---

## 📊 Conclusão

### Status Geral: ✅ **PASSANDO EM TODOS OS GATES**

O projeto atinge os requisitos mínimos de CI (ruff, mypy, cobertura ≥70%) e todos os testes passam. A cobertura geral está em 79.93%, muito próxima do objetivo ideal de 80% definido no CLAUDE.md. Os principais gaps remanescentes estão em código ligado a infraestrutura externa (Redis, ONNX) e configuração de logging, que não bloqueiam o MVP.
