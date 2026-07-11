"""Configuração do modelo base do SQLAlchemy."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Classe base para todos os modelos SQLAlchemy.

    Usa estilo declarativo do SQLAlchemy 2.0 com Mapped e mapped_column.
    """

    pass
