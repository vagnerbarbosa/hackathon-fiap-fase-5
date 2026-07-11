"""
Modelos Pydantic v2 compartilhados para entidades de domínio.

Estes modelos servem como a "lingua franca" entre todos os módulos do projeto.
"""

from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ── Detecção (Spec 003 produz) ───────────────────────────


class BoundingBox(BaseModel):
    """Coordenadas em pixels de um componente detectado."""

    x_min: int
    y_min: int
    x_max: int
    y_max: int


class Point(BaseModel):
    """Ponto central de um componente."""

    x: int
    y: int


class DetectedComponent(BaseModel):
    """Componente arquitetural individual detectado."""

    id: str  # UUID gerado
    type: str  # ex: "user", "api", "database"
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: BoundingBox
    center: Point


class DataFlow(BaseModel):
    """Conexão entre componentes."""

    source_id: str
    target_id: str
    direction: Literal["unidirectional", "bidirectional"]
    inferred: bool  # True = inferido por heurística


class ArchitectureGraph(BaseModel):
    """Resultado completo da detecção."""

    components: list[DetectedComponent]
    data_flows: list[DataFlow]
    trust_boundaries: list[list[str]]  # grupos de componentes por zona


# ── STRIDE (Spec 004 produz) ─────────────────────────────


class Severity(str, Enum):
    """Níveis de severidade de ameaças."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Threat(BaseModel):
    """Ameaça STRIDE individual identificada."""

    id: str
    category: str  # "S","T","R","I","D","E"
    component_id: str
    component_type: str
    description: str
    severity: Severity
    affected_data_flows: list[str] = []


# ── Vulnerabilidades (Spec 005 produz) ───────────────────


class Countermeasure(BaseModel):
    """Contramedida para uma ameaça."""

    title: str
    description: str
    owasp_ref: str | None = None


class EnrichedThreat(BaseModel):
    """Ameaça com dados de vulnerabilidade."""

    id: str
    category: str  # "S","T","R","I","D","E"
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
    """Status de processamento."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(BaseModel):
    """Rastreamento de job de análise."""

    id: UUID = Field(default_factory=uuid4)
    status: JobStatus
    input_image_path: str
    output_report_path: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


__all__ = [
    # Detection
    "BoundingBox",
    "Point",
    "DetectedComponent",
    "DataFlow",
    "ArchitectureGraph",
    # STRIDE
    "Severity",
    "Threat",
    # Vulnerability
    "Countermeasure",
    "EnrichedThreat",
    # Jobs
    "JobStatus",
    "Job",
]
