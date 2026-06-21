# Spec: Dataset e Treinamento de Modelo de Detecção de Componentes de Arquitetura

---

## Contexto / Motivação

O hackathon exige que construamos ou busquemos um dataset de imagens de arquitetura de software, anotemos para treinamento supervisionado, e treinemos um modelo capaz de identificar componentes de arquitetura (usuários, servidores, APIs, bases de dados, etc.).

## Objetivo

Criar um pipeline completo de:
1. **Aquisição/geração de dados**: Dataset de imagens de diagramas de arquitetura de software.
2. **Anotação**: Bounding boxes e labels no formato YOLO para detecção supervisionada.
3. **Treinamento**: Fine-tuning de YOLOv8 (ou similar) para detectar componentes de arquitetura.
4. **Validação**: Métricas de qualidade (mAP, precision, recall) nas arquiteturas de teste.

## Requisitos Funcionais (RF)

### RF-01: Criação do Dataset
- Gerar ou coletar no mínimo **100 imagens** de diagramas de arquitetura de software.
- As imagens devem conter variações de:
  - Tipos de componentes (usuário, web server, API, database, fila, cache, serviço externo, mobile app, etc.)
  - Layouts (horizontal, vertical, híbrido)
  - Estilos visuais (draw.io, Lucidchart, Excalidraw, PlantUML, hand-drawn, etc.)
  - Complexidade (2–10 componentes por diagrama)

### RF-02: Taxonomia de Componentes (Classes)
O dataset deve anotar as seguintes classes (ajustável conforme validação):

| ID | Classe | Descrição |
|----|--------|-----------|
| 0 | `user` | Usuário final / Cliente |
| 1 | `web_server` | Servidor web / Load balancer |
| 2 | `api` | API REST / GraphQL / Gateway |
| 3 | `database` | Base de dados relacional / NoSQL |
| 4 | `queue` | Fila / Message broker (RabbitMQ, Kafka, SQS) |
| 5 | `cache` | Cache (Redis, Memcached) |
| 6 | `external_service` | Serviço externo / Terceiro |
| 7 | `mobile_app` | Aplicativo mobile |
| 8 | `container` | Container / Pod (Kubernetes) |
| 9 | `storage` | Armazenamento de arquivos / Blob |

### RF-03: Anotação no Formato YOLO
- Cada imagem deve ter um arquivo `.txt` correspondente com o mesmo nome.
- Formato YOLO: `<class_id> <x_center> <y_center> <width> <height>` (valores normalizados 0–1).
- Utilizar ferramenta de anotação: [LabelImg](https://github.com/tzutalin/labelImg), [CVAT](https://cvat.org/), [Roboflow](https://roboflow.com/), ou script customizado.

### RF-04: Divisão Train/Val/Test
- `train/`: 70% das imagens
- `val/`: 20% das imagens
- `test/`: 10% das imagens (incluir as 2 arquiteturas de teste do hackathon)
- `data.yaml`: Configuração do dataset para Ultralytics YOLOv8.

### RF-05: Treinamento do Modelo
- Base: YOLOv8n (nano) ou YOLOv8s (small) — priorizar velocidade para MVP.
- Fine-tuning com dataset customizado.
- Hiperparâmetros sugeridos (ajustáveis):
  - `epochs: 100`
  - `imgsz: 640`
  - `batch: 16`
  - `device: 0` (GPU) ou `cpu`
  - `patience: 20` (early stopping)

### RF-06: Exportação do Modelo
- Exportar para ONNX (`best.onnx`) para inferência otimizada.
- Salvar modelo PyTorch (`best.pt`) para re-treinamento futuro.
- Documentar métricas finais: mAP@0.5, mAP@0.5:0.95, precision, recall.

### RF-07: Notebook Reproduzível
- Criar `notebooks/01_train_yolo.ipynb` com todo o pipeline:
  - Instalação de dependências
  - Download/geração do dataset
  - Treinamento
  - Validação
  - Exportação
  - Teste em imagem exemplo

## Requisitos Não-Funcionais (RNF)

### RNF-01: Qualidade do Dataset
- Balanceamento de classes: cada classe deve aparecer em pelo menos 15% das imagens.
- Resolução mínima: 640x480 px.
- Formato: PNG ou JPG.

### RNF-02: Reprodutibilidade
- Fixar seeds (`random`, `numpy`, `torch`).
- Versionar dataset com DVC ou documentar fonte/proveniência.
- Salvar `requirements-notebook.txt` com versões exatas.

### RNF-03: Métricas Mínimas
- `mAP@0.5` > 0.75 nas arquiteturas de teste.
- `mAP@0.5:0.95` > 0.50.

## Critérios de Aceitação

### CA-01: Dataset Criado
```gherkin
Dado que o pipeline de dataset foi executado
Então existem ≥100 imagens anotadas no formato YOLO
E o arquivo data.yaml está configurado corretamente
E as divisões train/val/test estão respeitadas
```

### CA-02: Modelo Treinado
```gherkin
Dado que o notebook de treinamento foi executado
Quando o treinamento converge
Então o modelo best.pt é gerado
E as métricas finais atendem os RNF de qualidade
```

### CA-03: Detecção nas Arquiteturas de Teste
```gherkin
Dado as 2 arquiteturas de teste do hackathon
Quando o modelo treinado faz inferência
Então detecta pelo menos 80% dos componentes esperados
E classifica corretamente os tipos (user, api, database, etc.)
```

## Dependências

### Bibliotecas
- `ultralytics==8.3.x`
- `opencv-python==4.10.x`
- `torch==2.4.x`
- `torchvision==0.19.x`
- `albumentations` (opcional, para augmentation)
- `roboflow` (opcional, para download/augmentation)

### Ferramentas de Anotação
- LabelImg (local)
- CVAT (online/self-hosted)
- Roboflow (online)

## Decisões Técnicas (ADR)

### ADR-001: Geração Sintética + Real
- **Contexto**: Difícil encontrar 100+ imagens reais de arquiteturas de software com permissão de uso.
- **Decisão**: Combinar geração sintética (scripts Python + Pillow/draw.io API) com imagens reais de repos públicos/documentação.
- **Justificativa**:
  - Permite controlar variabilidade (layouts, componentes, estilos).
  - Acelera criação do dataset.
  - Pode ser complementado com imagens reais para robustez.
- **Consequências**: Necessário validar que modelo generaliza para imagens reais. Risco de overfitting em padrões sintéticos.

### ADR-002: YOLOv8n como Backbone
- **Contexto**: MVP precisa ser rápido e funcional.
- **Decisão**: Usar YOLOv8n (nano) para treinamento e inferência rápidos.
- **Justificativa**:
  - ~3.2M parâmetros — treina em minutos/horas.
  - Inferência >100 FPS em GPU — ideal para API.
  - Já utilizado na Fase 4 (familiaridade).
- **Consequências**: Menor precisão que YOLOv8x, mas suficiente para MVP. Se necessário, upgrada para YOLOv8s/m.

## Arquivos Planejados

```
notebooks/
└── 01_train_yolo.ipynb          # Notebook reproduzível de treinamento
dataset/
├── data.yaml                   # Config YOLO
├── train/
│   ├── images/
│   └── labels/
├── val/
│   ├── images/
│   └── labels/
└── test/
    ├── images/
    └── labels/
scripts/
├── generate_synthetic_diagrams.py  # Geração de diagramas sintéticos
└── convert_annotations.py         # Conversão entre formatos de anotação
models/
└── .gitkeep                    # best.pt e best.onnx (não versionados no git)
```

---

*Spec criada em: 2026-06-21*
*Baseada em: Context7 (PyTorch, OpenCV, YOLO) + requisitos do PDF do hackathon*
