"""
Shared Pydantic v2 models for domain entities.

These models serve as the "lingua franca" between all project modules.
"""

from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ── Detecção (Spec 003 produz) ───────────────────────────


class BoundingBox(BaseModel):
    """Pixel coordinates of a detected component."""

    x_min: int
    y_min: int
    x_max: int
    y_max: int


class Point(BaseModel):
    """Center point of a component."""

    x: int
    y: int


class DetectedComponent(BaseModel):
    """Single detected architectural component."""

    id: str  # UUID gerado
    type: str  # ex: "user", "api", "database"
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: BoundingBox
    center: Point


class DataFlow(BaseModel):
    """Connection between components."""

    source_id: str
    target_id: str
    direction: Literal["unidirectional", "bidirectional"]
    inferred: bool  # True = inferido por heurística


class ArchitectureGraph(BaseModel):
    """Complete detection result."""

    components: list[DetectedComponent]
    data_flows: list[DataFlow]
    trust_boundaries: list[list[str]]  # grupos de componentes por zona


# ── STRIDE (Spec 004 produz) ─────────────────────────────


class Severity(str, Enum):
    """Threat severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Threat(BaseModel):
    """Ameaca STRIDE identificada."""

    id: str
    category: str  # "S","T","R","I","D","E"
    category_name: str  # "Spoofing", "Tampering", ...
    component_id: str
    component_type: str
    description: str
    justification: str
    severity: Severity
    affected_data_flows: list[str] = Field(default_factory=list)


# ── Vulnerabilidades (Spec 005 produz) ───────────────────


class Countermeasure(BaseModel):
    """Mitigation for a threat."""

    title: str
    description: str
    owasp_ref: str | None = None


class EnrichedThreat(BaseModel):
    """Ameaca enriquecida com dados de vulnerabilidade."""

    id: str
    category: str  # "S","T","R","I","D","E"
    category_name: str
    component_id: str
    component_type: str
    description: str
    justification: str
    severity: Severity
    cwe_id: str | None = None
    cwe_name: str | None = None
    cve_ids: list[str] = []
    countermeasures: list[Countermeasure] = []


# ── Jobs (Spec 001 produz / Spec 006 consome) ────────────


class JobStatus(str, Enum):
    """Processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(BaseModel):
    """Analysis job tracking."""

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
