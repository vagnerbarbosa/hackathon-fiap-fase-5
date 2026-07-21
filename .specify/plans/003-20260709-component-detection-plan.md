# Plano de Implementação: Component Detection Service (Spec 003)

**Feature**: 003-component-detection-service | **Branch**: `feature/003-component-detection`
**Status**: ✅ Completed

---

## Technical Context

### Stack
- Python 3.11+, FastAPI (async)
- Ultralytics YOLOv11 (model.predict())
- OpenCV 4.13.x (pré-processamento)
- ONNX Runtime (inferência otimizada)
- Redis (cache por hash de imagem)
- Pydantic v2 (models)

### Dependencies
- **Spec 000**: Contratos de domínio (`ArchitectureGraph`, `DetectedComponent`, `DataFlow`)
- **Spec 001**: Infrastructure (Redis, logging, config)
- **Spec 002**: Modelo treinado `best.pt` ou `best.onnx` (usa stub/mock por enquanto)

### Requisitos do Context7 (Obrigatório)
1. ONNX Runtime: `onnxruntime.InferenceSession("best.onnx", providers=["CUDAExecutionProvider", "CPUExecutionProvider"])`
   - Output shape: `[1, 34, 8400]` → `[batch, 4+30_classes, num_anchors]`
   - Sem campo de confiança separado; confiança = `max(class_scores[4:])`
2. OpenCV: redimensionamento para 640x640, normalização 0-1, conversão BGR→RGB
3. NMS: IoU threshold 0.45 para eliminar detecções duplicadas
4. Confidence threshold: 0.15 (mínimo para manter detecção)
5. Cache Redis: TTL 1 hora, chave = SHA-256 da imagem

---

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Spec-First | ✅ | Spec 003 já escrita |
| II. API First | ✅ | Contratos Pydantic definidos |
| III. Context7 | ✅ | Consultado YOLO, ONNX, OpenCV |
| IV. Pull Request Only | ✅ | Branch criada, PR após #9 merge |
| V. Test-First | ⚠️ | Mocks primeiro, testes antes da implementação |
| VI. Parallel Work | ✅ | Usa stub YOLO enquanto Spec 002 não termina |
| VII. Observability | ✅ | Logging JSON estruturado |
| VIII. Security | ✅ | Reusa validação de upload da Spec 001 |

---

## Phase 1: Design & Contracts

### Data Model

```python
# src/domain/models.py (já existe da Spec 000)
class BoundingBox(BaseModel):
    x_min: int
    y_min: int
    x_max: int
    y_max: int

class Point(BaseModel):
    x_center: float
    y_center: float

class DetectedComponent(BaseModel):
    id: str                     # UUID
    type: str                   # ex: "actor_user", "compute_service", "data_database"
    confidence: float           # 0.0-1.0
    bbox: BoundingBox
    center: Point

class DataFlow(BaseModel):
    source_id: str
    target_id: str
    direction: Literal["unidirectional", "bidirectional"]
    inferred: bool              # True = heurística espacial

class ArchitectureGraph(BaseModel):
    components: list[DetectedComponent]
    data_flows: list[DataFlow]
    trust_boundaries: list[list[str]]  # grupos de componentes
```

### Contracts (Internal)

**Input**: `image_path: str | Path` (já validado por magic bytes na Spec 001)

**Output**: `ArchitectureGraph` (vai para Spec 004)

### Quickstart (Validation Scenarios)

```python
# tests/mocks/fake_yolo_stub.py
class YOLOStub:
    """Mock do modelo YOLO para desenvolvimento paralelo."""
    
    def predict(self, image_path, conf=0.15, iou=0.45, imgsz=640):
        # Retorna resultados simulados (30 classes do dataset/data.yaml)
        return [MockResults([
            MockBox(cls="actor_user", conf=0.85, xyxy=[10, 50, 60, 100]),
            MockBox(cls="edge_gateway", conf=0.78, xyxy=[200, 50, 300, 120]),
            MockBox(cls="data_database", conf=0.91, xyxy=[400, 50, 500, 120]),
        ])]

# tests/mocks/fake_architecture_graph.py
fake_graph = ArchitectureGraph(
    components=[
        DetectedComponent(id="uuid-1", type="actor_user", confidence=0.85, ...),
        DetectedComponent(id="uuid-2", type="edge_gateway", confidence=0.78, ...),
        DetectedComponent(id="uuid-3", type="data_database", confidence=0.91, ...),
    ],
    data_flows=[
        DataFlow(source_id="uuid-1", target_id="uuid-2", direction="unidirectional", inferred=True),
        DataFlow(source_id="uuid-2", target_id="uuid-3", direction="unidirectional", inferred=True),
    ],
    trust_boundaries=[["uuid-1"], ["uuid-2"], ["uuid-3"]],
)
```

---

## Phase 2: Research Summary

### Context7 Findings

**YOLOv11 (Ultralytics)**:
- Carregar: `YOLO("path/to/best.pt")` (apenas para treinamento/debugging)
- Inferência em produção: via ONNX Runtime (mais rápido e leve)
- 30 classes definidas em `dataset/data.yaml`
- Mapear labels numéricos para nomes via dicionário de classes

**ONNX Runtime**:
- Carregar: `InferenceSession("best.onnx", providers=[...])`
- Inferência: `session.run(None, {input_name: preprocessed_image})`
- Output shape: `[1, 34, 8400]` = `[batch, 4_box + 30_classes, num_anchors]`
- Formato YOLOv11: **sem campo de confiança separado** — confiança = max(class_scores)
- ~2x mais rápido que PyTorch em CPU
- Threshold de confiança: 0.15 (aplicado pós-inferência)
- NMS com IoU threshold 0.45

**OpenCV**:
- `cv2.resize(img, (640, 640))` - múltiplo de 32
- `img.astype(np.float32) / 255.0` - normalização
- `cv2.cvtColor(img, cv2.COLOR_BGR2RGB)` - converter para RGB

**Redis Cache**:
- Chave: `detection:{sha256_hash}`
- Valor: JSON do ArchitectureGraph
- TTL: 3600 segundos (1 hora)

---

## Phase 3: Tasks

### Phase 1: Setup & Contracts
- [x] T001: Criar mocks YOLO stub em `tests/mocks/yolo_stub.py`
- [x] T002: Criar mock ArchitectureGraph em `tests/mocks/fake_architecture_graph.py`

### Phase 2: Infrastructure
- [x] T003: Criar `src/infrastructure/ml/yolo_model.py` - wrapper YOLO/ONNX
- [x] T004: Criar `src/infrastructure/cache/detection_cache.py` - cache Redis

### Phase 3: Services
- [x] T005: Criar `src/services/image_preprocessor.py` - OpenCV preprocessing
- [x] T006: Criar `src/services/relationship_analyzer.py` - heurística espacial
- [x] T007: Criar `src/services/component_detector.py` - orquestração

### Phase 4: API Integration
- [x] T008: Atualizar `src/api/routes/threat_model.py` - endpoint POST /analyze
- [x] T009: Adicionar serviço ao container de dependências

### Phase 5: Tests
- [x] T010: Testes unitários com mocks (`tests/unit/test_component_detector.py`)
- [x] T011: Testes de heurística (`tests/unit/test_relationship_analyzer.py`)
- [x] T012: Testes de integração E2E (`tests/integration/test_detection_e2e.py`)

### Phase 6: Documentation
- [x] T013: Atualizar README.md com instruções do serviço
- [~] T014: Documentar decisão ONNX vs PyTorch em `docs/adrs/` — Dispensada (documentada inline na spec 003)

---

## Task Summary

| Phase | Tasks | Focus |
|-------|-------|-------|
| Phase 1: Mocks | 2 | Stubs para paralelismo |
| Phase 2: Infrastructure | 2 | ML wrapper, cache |
| Phase 3: Services | 3 | Core detection logic |
| Phase 4: API | 2 | Integration |
| Phase 5: Tests | 3 | Unit + integration |
| Phase 6: Docs | 2 | ADR, README |

**Total Tasks**: 14
**Depends on**: Spec 001 (mergeada → main), Spec 002 (apenas modelo best.pt)

---

## Nota sobre Dependências

Esta branch (`feature/003-component-detection`) foi criada a partir de `feature/001-api-core`.

**Antes de abrir a PR**:
1. Aguardar merge da PR #9 (Spec 001)
2. Rebase `feature/003-component-detection` em `main` atualizada
3. Verificar se modelo `best.pt` da Spec 002 está disponível em `models/`
4. Abrir PR #? para review

**Se modelo não estiver pronto**:
- Usar `YOLOStub` em dev
- Testes unitários passam com mocks
- Testes E2E são skipados até modelo estar disponível

---

*Plano criado em: 2026-07-09*
*Baseado em: Spec 003 + Context7 (YOLO, ONNX, OpenCV)*
