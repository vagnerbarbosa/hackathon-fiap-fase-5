"""Carregamento e validacao dos mapeamentos STRIDE."""

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError


VALID_STRIDE_CATEGORIES = {"S", "T", "R", "I", "D", "E"}
STRIDE_MAPPINGS_PATH_ENV = "STRIDE_MAPPINGS_PATH"
DEFAULT_STRIDE_MAPPINGS_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "stride_mappings.yaml"
)


class StrideMappingError(ValueError):
    """Erro para arquivo de mapeamento ausente ou invalido."""


class MappingThreat(BaseModel):
    """Definicao interna de ameaca carregada do YAML."""

    category: str
    description: str
    justification: str


class _ComponentMapping(BaseModel):
    threats: list[MappingThreat]


class _DataFlowMapping(BaseModel):
    threats: list[MappingThreat]


class _StrideMappingDocument(BaseModel):
    components: dict[str, _ComponentMapping]
    data_flows: _DataFlowMapping


class StrideMappings:
    """Acesso aos mapeamentos STRIDE de componentes e fluxos."""

    def __init__(self, document: _StrideMappingDocument) -> None:
        self._document = document

    @classmethod
    def from_file(cls, path: Path = DEFAULT_STRIDE_MAPPINGS_PATH) -> "StrideMappings":
        """Carrega e valida mapeamentos a partir de YAML."""
        try:
            raw_content = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise StrideMappingError(f"Unable to read STRIDE mappings: {path}") from exc

        try:
            raw_data = yaml.safe_load(raw_content)
        except yaml.YAMLError as exc:
            raise StrideMappingError(f"Invalid YAML in STRIDE mappings: {path}") from exc

        if not isinstance(raw_data, dict):
            raise StrideMappingError("STRIDE mappings must be a YAML object.")

        try:
            document = _StrideMappingDocument.model_validate(raw_data)
        except ValidationError as exc:
            raise StrideMappingError(f"Invalid STRIDE mapping structure: {exc}") from exc

        cls._validate_categories(document)
        return cls(document)

    def get_component_threats(self, component_type: str) -> list[MappingThreat]:
        """Retorna ameacas configuradas para um tipo de componente."""
        component = self._document.components.get(component_type.lower())
        if component is None:
            return []
        return list(component.threats)

    def has_component_type(self, component_type: str) -> bool:
        """Indica se o tipo de componente existe no mapeamento."""
        return component_type.lower() in self._document.components

    def get_data_flow_threats(self) -> list[MappingThreat]:
        """Retorna ameacas configuradas para fluxos de dados."""
        return list(self._document.data_flows.threats)

    @staticmethod
    def _validate_categories(document: _StrideMappingDocument) -> None:
        invalid_categories: list[str] = []

        def collect_invalid(threats: list[MappingThreat]) -> None:
            for threat in threats:
                if threat.category not in VALID_STRIDE_CATEGORIES:
                    invalid_categories.append(threat.category)

        for component in document.components.values():
            collect_invalid(component.threats)
        collect_invalid(document.data_flows.threats)

        if invalid_categories:
            categories = ", ".join(sorted(set(invalid_categories)))
            raise StrideMappingError(f"Invalid STRIDE categories: {categories}")


def default_stride_mappings_path() -> Path:
    """Resolve o caminho padrao, permitindo override por ambiente."""
    configured_path = os.environ.get(STRIDE_MAPPINGS_PATH_ENV)
    if configured_path:
        return Path(configured_path)
    return DEFAULT_STRIDE_MAPPINGS_PATH
