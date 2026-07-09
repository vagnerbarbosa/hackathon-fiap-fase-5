"""SQLAlchemy base model configuration."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    Uses SQLAlchemy 2.0 declarative style with Mapped and mapped_column.
    """

    pass
