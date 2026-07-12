# Tasks: Component Detection Service (Spec 003)

**Feature**: 003-component-detection-service | **Branch**: `feature/003-component-detection`

**Depends on**: Spec 001 (mergeada), Spec 002 (modelo best.pt - usa stub se não pronto)

---

## Phase 1: Mocks — Parallel Development Support

Criar stubs/mocks para permitir desenvolvimento sem o modelo YOLO treinado.

- [ ] T001 Create `tests/mocks/yolo_stub.py` with `YOLOStub` class
  - Método `predict()` que retorna resultados simulados
  - Atributo `names` com mapeamento de classes
  - Simular boxes com cls, conf, xyxy

- [ ] T002 Create `tests/mocks/fake_architecture_graph.py`
  - Instância `fake_graph` com 2-3 componentes
  - DataFlows e trust boundaries de exemplo
  - Usar para testes enquanto Spec 002 não termina

---

## Phase 2: Infrastructure — ML & Cache

Implementar wrappers para modelo e cache.

- [ ] T003 Create `src/infrastructure/ml/yolo_model.py`
  - Classe `YOLOModel` com suporte a .pt e .onnx
  - Método `load_model(path)` com detecção de extensão
  - Método `predict(image_path)` retornando detecções
  - Singleton pattern (carrega uma única vez)
  - Fallback para stub se modelo não existir

- [ ] T004 Create `src/infrastructure/cache/detection_cache.py`
  - Classe `DetectionCache` com Redis
  - Método `get(image_hash)` → ArchitectureGraph | None
  - Método `set(image_hash, graph)` com TTL=3600
  - Método `_compute_hash(image_path)` SHA-256

---

## Phase 3: Services — Core Logic

Implementar os serviços de detecção.

- [ ] T005 Create `src/services/image_preprocessor.py`
  - Classe `ImagePreprocessor`
  - Método `preprocess(image_path)` → numpy array
  - Redimensionar para múltiplo de 32 (640x640)
  - Normalizar pixels (0-255 → 0-1)
  - Converter para RGB se necessário
  - Binarização opcional (threshold adaptativo)

- [ ] T006 Create `src/services/relationship_analyzer.py`
  - Classe `RelationshipAnalyzer`
  - Método `analyze(components)` → DataFlows, TrustBoundaries
  - Heurística de proximidade espacial
  - Regras: user→público, database→privado, api→fronteira
  - Marcar fluxos como inferred=True

- [ ] T007 Create `src/services/component_detector.py`
  - Classe `ComponentDetectionService` (orquestradora)
  - Método `detect(image_path)` → ArchitectureGraph
  - Fluxo: cache? → preprocess → YOLO predict → analyze relationships → cache result
  - Tratamento de erro NO_COMPONENTS_DETECTED

---

## Phase 4: API Integration

Integrar com a API FastAPI da Spec 001.

- [ ] T008 Update `src/api/routes/threat_model.py`
  - Implementar POST /api/v1/threat-model/analyze
  - Receber upload de imagem (usa validação da Spec 001)
  - Chamar ComponentDetectionService
  - Retornar job_id + ArchitectureGraph
  - Headers de segurança OWASP (reuso da Spec 001)

- [ ] T009 Add dependency injection
  - Injetar ComponentDetectionService em routes
  - Configurar singleton no lifespan da aplicação

---

## Phase 5: Tests

Testes unitários e de integração.

- [ ] T010 Create `tests/unit/test_component_detector.py`
  - Testar com YOLOStub (mock)
  - Testar cache hit/miss
  - Testar fallback NO_COMPONENTS_DETECTED
  - Coverage >= 70%

- [ ] T011 Create `tests/unit/test_relationship_analyzer.py`
  - Testar heurística espacial
  - Testar regras de trust boundaries
  - Mock de componentes fictícios

- [ ] T012 Create `tests/integration/test_detection_e2e.py`
  - Teste E2E com imagem real (requer best.pt)
  - Skip se modelo não disponível (`pytest.skip`)
  - Verificar tempo de resposta < 10s (CPU)

---

## Phase 6: Documentation & Polish

Documentação e ajustes finais.

- [ ] T013 Update README.md
  - Documentar uso do serviço de detecção
  - Instruções para colocar modelo em `models/`
  - Como usar YOLOStub em desenvolvimento

- [ ] T014 Create `docs/adrs/003-onnx-vs-pytorch.md`
  - Documentar decisão de suportar ambos
  - Justificativa: performance ONNX, flexibilidade PyTorch

---

## Phase 7: Cross-Platform Scripts

Atualizar scripts de inicialização.

- [ ] T015 Update `scripts/start-api.sh` (e .ps1, .py)
  - Verificar se diretório `models/` existe
  - Mensagem informativa se modelo não encontrado (usa stub)
  - Mount volume `models/` no docker-compose se necessário

---

## Task Summary

| Phase | Tasks | Focus | Parallelizable |
|-------|-------|-------|----------------|
| Phase 1: Mocks | 2 | Stubs for parallel work | Yes |
| Phase 2: Infrastructure | 2 | ML wrapper, Redis cache | Yes |
| Phase 3: Services | 3 | Core detection logic | No (sequential) |
| Phase 4: API Integration | 2 | FastAPI endpoints | No |
| Phase 5: Tests | 3 | Unit + integration | Yes (2) |
| Phase 6: Documentation | 2 | ADR, README | Yes |
| Phase 7: Scripts | 1 | Cross-platform updates | No |

**Total Tasks**: 15
**Parallel Tasks**: 7
**Sequential Tasks**: 8

---

## Dependencies Between Tasks

```
T001, T002 (mocks)
    |
    +--> T003 (YOLO wrapper - can use stub)
    |       |
    |       +--> T005 (preprocessor)
    |       +--> T007 (service - depends on T003, T005, T006)
    |
    +--> T004 (cache)
            |
            +--> T007 (service)

T006 (relationship analyzer) --> T007

T007 (service) --> T008 (API routes)

T007 --> T010 (unit tests)
T006 --> T011 (analyzer tests)
T007 + best.pt --> T012 (E2E tests)
```

---

## Notes

- Usar mocks/stubs até Spec 002 terminar
- Testes E2E devem usar `pytest.mark.skipif` se modelo não existir
- Manter compatibilidade com contratos Spec 000 (models.py)
- Reusar configurações de Redis da Spec 001

*Tasks created: 2026-07-09*
*Plan: .specify/plans/003-20260709-component-detection-plan.md*
