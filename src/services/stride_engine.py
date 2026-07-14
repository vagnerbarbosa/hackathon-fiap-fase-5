"""Motor de analise de ameacas STRIDE baseado em regras."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from src.core.stride_mappings import (
    MappingThreat,
    StrideMappings,
    default_stride_mappings_path,
)
from src.core.stride_rules import calculate_severity, category_name, severity_sort_rank
from src.domain.models import ArchitectureGraph, DataFlow, Threat


DATA_FLOW_COMPONENT_TYPE = "data_flow"
logger = logging.getLogger(__name__)

TRUST_BOUNDARY_THREATS = [
    MappingThreat(
        category="S",
        description="Identidades podem ser falsificadas ao cruzar trust boundary.",
        justification="Cruzamentos entre zonas de confianca exigem autenticacao explicita.",
    ),
    MappingThreat(
        category="T",
        description="Dados podem ser alterados ao cruzar trust boundary.",
        justification="O fluxo passa por uma fronteira onde controles de integridade mudam.",
    ),
    MappingThreat(
        category="R",
        description="Eventos podem ser negados ao cruzar trust boundary.",
        justification="A correlacao de auditoria entre zonas distintas pode falhar.",
    ),
    MappingThreat(
        category="I",
        description="Dados podem ser expostos ao cruzar trust boundary.",
        justification="A fronteira pode separar dominios com politicas de confidencialidade diferentes.",
    ),
    MappingThreat(
        category="D",
        description="O canal pode sofrer indisponibilidade ao cruzar trust boundary.",
        justification="Controles e limites entre zonas podem ser abusados para degradar o fluxo.",
    ),
    MappingThreat(
        category="E",
        description="Privilegios podem ser ampliados ao cruzar trust boundary.",
        justification="A transicao entre dominios de confianca pode expor autorizacoes indevidas.",
    ),
]


class StrideEngine:
    """Analisa um grafo de arquitetura e produz ameacas STRIDE."""

    def __init__(
        self,
        mappings: StrideMappings | None = None,
        mappings_path: Path | None = None,
    ) -> None:
        self._mappings = mappings or StrideMappings.from_file(
            mappings_path or default_stride_mappings_path()
        )

    async def analyze(self, graph: ArchitectureGraph) -> list[Threat]:
        """Aplica STRIDE preservando assinatura async exigida pela Spec 004."""
        mappings = self._mappings
        component_by_id = {component.id: component for component in graph.components}
        boundary_by_component = self._build_boundary_index(graph.trust_boundaries)

        threats: list[Threat] = []

        for component in graph.components:
            component_threats = mappings.get_component_threats(component.type)
            if not component_threats and not mappings.has_component_type(component.type):
                self._log_unknown_component_type(
                    component_id=component.id,
                    component_type=component.type,
                )

            for mapping in component_threats:
                threats.append(
                    self._build_component_threat(
                        component_id=component.id,
                        component_type=component.type,
                        mapping=mapping,
                    )
                )

        for flow in graph.data_flows:
            if (
                flow.source_id not in component_by_id
                or flow.target_id not in component_by_id
            ):
                continue

            crosses_trust_boundary = self._crosses_trust_boundary(
                flow=flow,
                boundary_by_component=boundary_by_component,
            )
            for mapping in mappings.get_data_flow_threats():
                threats.append(
                    self._build_data_flow_threat(
                        flow=flow,
                        mapping=mapping,
                        crosses_trust_boundary=crosses_trust_boundary,
                    )
                )
            if crosses_trust_boundary:
                for mapping in TRUST_BOUNDARY_THREATS:
                    threats.append(
                        self._build_data_flow_threat(
                            flow=flow,
                            mapping=mapping,
                            crosses_trust_boundary=True,
                        )
                    )

        return self._sort_threats(self._deduplicate(threats))

    @staticmethod
    def _build_boundary_index(
        trust_boundaries: list[list[str]],
    ) -> dict[str, int]:
        return {
            component_id: index
            for index, boundary in enumerate(trust_boundaries)
            for component_id in boundary
        }

    @staticmethod
    def _crosses_trust_boundary(
        *,
        flow: DataFlow,
        boundary_by_component: dict[str, int],
    ) -> bool:
        source_boundary = boundary_by_component.get(flow.source_id)
        target_boundary = boundary_by_component.get(flow.target_id)
        if source_boundary is None or target_boundary is None:
            return False
        return source_boundary != target_boundary

    @staticmethod
    def _flow_id(flow: DataFlow) -> str:
        return f"flow:{flow.source_id}:{flow.target_id}:{flow.direction}"

    @staticmethod
    def _component_threat_id(component_id: str, category: str) -> str:
        return f"threat:{component_id}:{category}"

    @classmethod
    def _data_flow_threat_id(cls, flow: DataFlow, category: str) -> str:
        return f"threat:{cls._flow_id(flow)}:{category}"

    @classmethod
    def _build_component_threat(
        cls,
        *,
        component_id: str,
        component_type: str,
        mapping: MappingThreat,
    ) -> Threat:
        return Threat(
            id=cls._component_threat_id(component_id, mapping.category),
            category=mapping.category,
            category_name=category_name(mapping.category),
            component_id=component_id,
            component_type=component_type,
            description=mapping.description,
            justification=mapping.justification,
            severity=calculate_severity(component_type, mapping.category),
            affected_data_flows=[],
        )

    @classmethod
    def _build_data_flow_threat(
        cls,
        *,
        flow: DataFlow,
        mapping: MappingThreat,
        crosses_trust_boundary: bool,
    ) -> Threat:
        flow_id = cls._flow_id(flow)
        description = mapping.description
        justification = mapping.justification
        if crosses_trust_boundary:
            description = f"{description} Cruza trust boundary."
            justification = f"{justification} O fluxo cruza uma trust boundary."

        return Threat(
            id=cls._data_flow_threat_id(flow, mapping.category),
            category=mapping.category,
            category_name=category_name(mapping.category),
            component_id=flow_id,
            component_type=DATA_FLOW_COMPONENT_TYPE,
            description=description,
            justification=justification,
            severity=calculate_severity(
                DATA_FLOW_COMPONENT_TYPE,
                mapping.category,
                crosses_trust_boundary=crosses_trust_boundary,
            ),
            affected_data_flows=[flow_id],
        )

    @staticmethod
    def _log_unknown_component_type(
        *,
        component_id: str,
        component_type: str,
    ) -> None:
        logger.warning(
            json.dumps(
                {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "level": "warning",
                    "module": __name__,
                    "message": "Unknown component type in STRIDE analysis.",
                    "request_id": None,
                    "component_id": component_id,
                    "component_type": component_type,
                },
                sort_keys=True,
            )
        )

    @staticmethod
    def _deduplicate(threats: list[Threat]) -> list[Threat]:
        deduplicated: dict[
            tuple[str, str, str, tuple[str, ...]],
            Threat,
        ] = {}

        for threat in threats:
            key = (
                threat.component_id,
                threat.component_type,
                threat.category,
                tuple(sorted(threat.affected_data_flows)),
            )
            current = deduplicated.get(key)
            if current is None or (
                severity_sort_rank(threat.severity)
                < severity_sort_rank(current.severity)
            ):
                deduplicated[key] = threat

        return list(deduplicated.values())

    @staticmethod
    def _sort_threats(threats: list[Threat]) -> list[Threat]:
        return sorted(
            threats,
            key=lambda threat: (
                severity_sort_rank(threat.severity),
                threat.category,
                threat.component_type,
                threat.component_id,
                threat.id,
            ),
        )


__all__ = ["StrideEngine"]
