# Spec 000 — Contratos de Domínio (Shared Models)

---

## Contexto / Motivação

Todas as specs (001–009) precisam compartilhar os mesmos tipos de dados para garantir consistência entre módulos. Esta spec define os **contratos de domínio** (models Pydantic v2) que são a "lingua franca" do projeto.

> **Regra de ouro**: ninguém altera estes models sem avisar no grupo e abrir PR exclusiva.

---

## Objetivo

Entregar `src/domain/models.py` com todos os tipos compartilhados + `tests/mocks/` com stubs prontos para uso em desenvolvimento paralelo.

---

## Contratos Definidos

### Modelos de Entrada/Saída (detecção → STRIDE → relatório)

```python
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum
from typing import Literal

# ── Detecção (Spec 003 produz) ───────────────────────────

class BoundingBox(BaseModel):
    x_min: int
    y_min: int
    x_max: int
    y_max: int

class Point(BaseModel):
    x: int
    y: int

class DetectedComponent(BaseModel):
    id: str                         # UUID gerado
    type: str                       # ex: "user", "api", "database"
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: BoundingBox
    center: Point

class DataFlow(BaseModel):
    source_id: str
    target_id: str
    direction: Literal["unidirectional", "bidirectional"]
    inferred: bool                  # True = inferido por heurística

class ArchitectureGraph(BaseModel):
    components: list[DetectedComponent]
    data_flows: list[DataFlow]
    trust_boundaries: list[list[str]]   # grupos de componentes por zona


# ── STRIDE (Spec 004 produz) ─────────────────────────────

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class Threat(BaseModel):
    id: str
    category: str                   # "S","T","R","I","D","E"
    component_id: str
    component_type: str
    description: str
    severity: Severity
    affected_data_flows: list[str] = []


# ── Vulnerabilidades (Spec 005 produz) ───────────────────

class Countermeasure(BaseModel):
    title: str
    description: str
    owasp_ref: str | None = None

class EnrichedThreat(BaseModel):
    id: str
    category: str
    component_id: str
    component_type: str
    description: str
    severity: Severity
    cwe_id: str | None = None
    cwe_name: str | None = None
    cve_ids: list[str] = []
    countermeasures: list[Countermeasure] = []


# ── Jobs (Spec 001 produz / Spec 006 consome) ────────────

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Job(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    status: JobStatus
    input_image_path: str
    output_report_path: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
```

---

## Mocks / Stubs para Testes Paralelos

Cada membro pode copiar os mocks abaixo para sua spec enquanto aguarda a implementação real.

### Mock `ArchitectureGraph` (para Spec 004 e 006)

```python
# tests/mocks/fake_architecture_graph.py
from uuid import uuid4
from domain.models import (
    ArchitectureGraph, DetectedComponent, DataFlow,
    BoundingBox, Point
)

fake_graph = ArchitectureGraph(
    components=[
        DetectedComponent(
            id=str(uuid4()), type="user", confidence=0.95,
            bbox=BoundingBox(x_min=10, y_min=50, x_max=60, y_max=100),
            center=Point(x=35, y=75),
        ),
        DetectedComponent(
            id=str(uuid4()), type="api", confidence=0.91,
            bbox=BoundingBox(x_min=200, y_min=50, x_max=300, y_max=120),
            center=Point(x=250, y=85),
        ),
        DetectedComponent(
            id=str(uuid4()), type="database", confidence=0.88,
            bbox=BoundingBox(x_min=400, y_min=60, x_max=480, y_max=110),
            center=Point(x=440, y=85),
        ),
    ],
    data_flows=[
        DataFlow(source_id="comp-1", target_id="comp-2",
                 direction="unidirectional", inferred=True),
        DataFlow(source_id="comp-2", target_id="comp-3",
                 direction="unidirectional", inferred=True),
    ],
    trust_boundaries=[["comp-1"], ["comp-2", "comp-3"]],
)
```

### Mock `Threat` (para Spec 005 e 006)

```python
# tests/mocks/fake_threats.py
from uuid import uuid4
from domain.models import Threat, Severity

fake_threats = [
    Threat(
        id=str(uuid4()), category="T", component_id="comp-db-1",
        component_type="database",
        description="Possibilidade de alteração não autorizada dos dados em repouso.",
        severity=Severity.HIGH, affected_data_flows=[],
    ),
    Threat(
        id=str(uuid4()), category="I", component_id="comp-db-1",
        component_type="database",
        description="Exfiltração de dados sensíveis sem criptografia.",
        severity=Severity.CRITICAL, affected_data_flows=[],
    ),
    Threat(
        id=str(uuid4()), category="D", component_id="comp-api-1",
        component_type="api",
        description="Negação de serviço por falta de rate limiting.",
        severity=Severity.MEDIUM, affected_data_flows=["flow-1"],
    ),
]
```

### Mock `EnrichedThreat` (para Spec 006)

```python
# tests/mocks/fake_enriched_threats.py
from uuid import uuid4
from domain.models import EnrichedThreat, Severity, Countermeasure

fake_enriched = [
    EnrichedThreat(
        id=str(uuid4()), category="T", component_id="comp-db-1",
        component_type="database",
        description="Possibilidade de alteração não autorizada dos dados em repouso.",
        severity=Severity.HIGH,
        cwe_id="CWE-522", cwe_name="Insufficiently Protected Credentials",
        cve_ids=["CVE-2023-1234"],
        countermeasures=[
            Countermeasure(
                title="TLS 1.3",
                description="Criptografia em trânsito.",
                owasp_ref="Cheat Sheet: Transport Layer Protection",
            ),
            Countermeasure(
                title="AES-256",
                description="Criptografia em repouso.",
                owasp_ref="Cheat Sheet: Cryptographic Storage",
            ),
        ],
    ),
]
```

### Mock `Job` (para Spec 006)

```python
# tests/mocks/fake_job.py
from uuid import uuid4
from datetime import datetime, timezone
from domain.models import Job, JobStatus

fake_job = Job(
    id=uuid4(), status=JobStatus.COMPLETED,
    input_image_path="/uploads/diagrama.png",
    output_report_path="/reports/job-123/report.md",
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc),
)
```

---

## Arquivos Entregáveis

| Arquivo | Responsabilidade |
|---------|------------------|
| `src/domain/__init__.py` | Pacote domain |
| `src/domain/models.py` | Todos os models Pydantic |
| `tests/mocks/fake_architecture_graph.py` | Stub para 004 e 006 |
| `tests/mocks/fake_threats.py` | Stub para 005 e 006 |
| `tests/mocks/fake_enriched_threats.py` | Stub para 006 |
| `tests/mocks/fake_job.py` | Stub para 006 |

---

## Dependências

### Nenhuma (esta é a primeira spec)

Esta spec não depende de nenhuma outra. É o alicerce.

---

## Critérios de Aceitação

### CA-01: Models Importáveis
```gherkin
Dado que a spec 000 está implementada
Quando importo from domain.models import ArchitectureGraph
Então a importação funciona sem erros
E todos os campos possuem type hints corretos
```

### CA-02: Mocks Funcionam
```gherkin
Dado que executo os mocks em tests/mocks/
Quando instancio fake_graph, fake_threats, fake_enriched, fake_job
Então todos os objetos validam corretamente com Pydantic v2
```

---

*Spec criada em: 2026-06-21*
*Responsável: Vagner Barbosa (@vagnerbarbosa)*
