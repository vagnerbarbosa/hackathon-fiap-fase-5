# Spec: Serviço de Detecção de Componentes de Arquitetura

---

## Contexto / Motivação

O core do MVP é interpretar automaticamente um diagrama de arquitetura de software em imagem e identificar seus componentes (usuários, servidores, APIs, bases de dados, etc.). Esta spec isola o serviço de inferência de Computer Vision, consumindo o modelo treinado na Spec 002 e expondo uma interface clara para o resto da aplicação.

## Objetivo

Implementar um serviço `ComponentDetectionService` que:
1. Recebe um path de imagem (local ou remoto).
2. Pré-processa a imagem para otimizar a detecção.
3. Executa inferência com o modelo YOLOv11n (ou YOLOv8n fallback) treinado (Spec 002).
4. Retorna uma lista estruturada de componentes detectados: tipo, bounding box, confiança.
5. Infere fluxos de dados (Data Flows) e trust boundaries com base na posição espacial dos componentes.

## Requisitos Funcionais (RF)

### RF-01: Interface do Serviço
```python
class DetectedComponent(BaseModel):
    id: str                     # UUID gerado
    type: str                   # ex: "user", "api", "database"
    confidence: float           # 0.0–1.0
    bbox: BoundingBox           # x_min, y_min, x_max, y_max (pixels)
    center: Point             # x_center, y_center (pixels)

class DataFlow(BaseModel):
    source_id: str
    target_id: str
    direction: str              # "unidirectional" | "bidirectional"
    inferred: bool              # True = inferido por heurística espacial

class ArchitectureGraph(BaseModel):
    components: list[DetectedComponent]
    data_flows: list[DataFlow]
    trust_boundaries: list[list[str]]  # grupos de componentes por zona de confiança

class ComponentDetectionService:
    async def detect(self, image_path: str | Path) -> ArchitectureGraph:
        ...
```

### RF-02: Pré-processamento de Imagem
- Redimensionar para múltiplo de 32 (ex: 640x640) — requisito do YOLO.
- Normalizar pixels (0–255 → 0–1).
- Conversão para RGB se necessário.
- Binarização opcional para diagramas com fundo escuro (threshold adaptativo via OpenCV).
- Suporte a PNG, JPG, JPEG (validação por magic bytes já feita na Spec 001).

### RF-03: Inferência com YOLOv8
- Carregar modelo `best.pt` (ou `best.onnx` para performance) exportado na Spec 002.
- Executar `model.predict()` com:
  - `conf=0.25` (threshold mínimo de confiança)
  - `iou=0.45` (threshold NMS)
  - `imgsz=640`
- Mapear labels numéricos do YOLO para nomes de classes (taxonomia definida na Spec 002).

### RF-04: Inferência de Relacionamentos (Heurística Espacial)
Com base nas posições (centros) dos componentes detectados, inferir:
- **Data Flows**: se dois componentes estão alinhados horizontalmente/verticalmente com proximidade < X pixels, inferir um fluxo.
- **Trust Boundaries**: agrupar componentes por zonas (ex: "público", "privado", "database") com base em regras:
  - `user` sempre está na zona "pública" (Internet).
  - `database` sempre está na zona "privada" (Data Layer).
  - `api` é fronteira entre público e privado.
- Marcar fluxos como `inferred: True` para diferenciar de futuras detecções explícitas.

### RF-05: Cache de Resultados
- Usar Redis (já configurado na Spec 001) para cachear resultados de detecção por hash da imagem (SHA-256).
- TTL: 1 hora.
- Se a mesma imagem for enviada novamente, retornar resultado cacheado.

### RF-06: Fallback em caso de falha do modelo
- Se o modelo não detectar nenhum componente (lista vazia), retornar erro amigável:
  ```json
  {
    "error": "NO_COMPONENTS_DETECTED",
    "message": "Nenhum componente de arquitetura foi detectado na imagem. Verifique se o diagrama está legível e contém componentes suportados.",
    "supported_types": ["user", "web_server", "api", "database", "queue", "cache", "external_service", "mobile_app", "container", "storage"]
  }
  ```

## Requisitos Não-Funcionais (RNF)

### RNF-01: Performance
- Inferência em GPU: < 3 segundos para imagem 640x640.
- Inferência em CPU: < 10 segundos.
- O serviço deve rodar assíncrono (não bloquear a thread principal da API).

### RNF-02: Memória
- Modelo deve ser carregado uma única vez na memória (singleton).
- Limite de memória para processamento de imagem: < 2GB.

### RNF-03: Testabilidade
- Mock do modelo YOLO para testes unitários (sem carregar pesos reais).
- Testes para heurística de relacionamentos com componentes fictícios.

## Critérios de Aceitação

### CA-01: Detecção de Componentes
```gherkin
Dado uma imagem de diagrama de arquitetura válida
Quando o serviço ComponentDetectionService.detect() é chamado
Então retorna uma lista de DetectedComponent
E cada componente tem type, confidence, bbox e center preenchidos
E confidence >= 0.25 para todos os componentes
```

### CA-02: Inferência de Fluxos
```gherkin
Dado uma imagem com um usuário à esquerda e uma API à direita
Quando o serviço detecta os componentes
Então infere um DataFlow de "user" para "api"
E marca como inferred: True
```

### CA-03: Cache
```gherkin
Dado que a mesma imagem foi analisada anteriormente
Quando o serviço recebe a imagem novamente
Então retorna o resultado do cache em < 100ms
```

### CA-04: Fallback
```gherkin
Dado uma imagem sem diagrama de arquitetura
Quando o serviço tenta detectar componentes
Então retorna erro NO_COMPONENTS_DETECTED com mensagem amigável
```

## Dependências

### Internas
- **Spec 001** — depende da estrutura de `src/services/`, `src/infrastructure/`, config, logging
- **Spec 002** — depende do modelo treinado (`best.pt` / `best.onnx`)

### Bibliotecas Python
- `ultralytics>=8.3.0` (suporta YOLOv11)
- `opencv-python==4.13.x`
- `torch==2.11.x` (se usar .pt) ou `onnxruntime` (se usar .onnx)
- `redis>=5.0.0` (para cache)

## Decisões Técnicas (ADR)

### ADR-001: ONNX Runtime vs PyTorch para Inferência
- **Contexto**: Precisamos escolher entre carregar o modelo .pt (PyTorch) ou exportar para .onnx (ONNX Runtime).
- **Decisão**: Suportar ambos, com prioridade para ONNX em produção.
- **Justificativa**:
  - ONNX Runtime é mais rápido e leve que PyTorch puro (~2x speedup em CPU).
  - Menor consumo de memória.
  - PyTorch .pt mantido para re-treinamento e debugging.
- **Consequências**: Dois artefatos de modelo. Dockerfile precisa instalar `onnxruntime` adicional.

### ADR-002: Heurística Espacial para Relacionamentos
- **Contexto**: Diagramas de arquitetura não têm setas explicitamente anotadas no dataset YOLO (foco em componentes).
- **Decisão**: Inferir relacionamentos por proximidade espacial + regras de domínio.
- **Justificativa**:
  - Anotar setas/fluxos em 100+ imagens é trabalhoso e fora do escopo do MVP.
  - Heurística espacial cobre 80% dos casos comuns (usuário → API → DB).
  - Pode ser aprimorado futuramente com OCR ou detecção de setas.
- **Consequências**: Relacionamentos podem ser imprecisos em layouts complexos. Documentar limitação.

## Módulos Planejados

| Arquivo | Responsabilidade |
|---------|------------------|
| `src/services/component_detector.py` | `ComponentDetectionService` — orquestração |
| `src/services/image_preprocessor.py` | Redimensionamento, normalização, binarização |
| `src/services/relationship_analyzer.py` | Heurística espacial para Data Flows e Trust Boundaries |
| `src/infrastructure/ml/yolo_model.py` | Wrapper para carregar YOLO/ONNX e executar predict |
| `src/infrastructure/cache/redis_cache.py` | Cache de resultados por hash de imagem |
| `tests/unit/test_component_detector.py` | Mock do modelo + testes de lógica |
| `tests/unit/test_relationship_analyzer.py` | Testes com componentes fictícios |
| `tests/integration/test_detection_e2e.py` | Teste end-to-end com imagem real (usa best.pt) |

---

*Spec criada em: 2026-06-21*
