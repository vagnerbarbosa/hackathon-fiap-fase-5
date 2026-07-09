"""Job model for threat modeling analysis."""

from datetime import datetime, timezone
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class JobStatus(str, PyEnum):
    """Job processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(Base):
    """Threat modeling analysis job.

    Represents an analysis request from image upload to report generation.
    """

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=JobStatus.PENDING.value,
        nullable=False,
    )
    input_image_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    output_report_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, status={self.status})>"
