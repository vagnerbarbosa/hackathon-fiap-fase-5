"""Rule-based STRIDE threat analysis engine."""

from core.stride_mappings import (
    DEFAULT_STRIDE_MAPPINGS_PATH,
    MappingThreat,
    StrideMappings,
)
from core.stride_rules import calculate_severity, severity_sort_rank
from domain.models import ArchitectureGraph, DataFlow, Threat


DATA_FLOW_COMPONENT_TYPE = "data_flow"


class StrideEngine:
    """Analyze an architecture graph and produce STRIDE threats."""

    def __init__(self, mappings: StrideMappings | None = None) -> None:
        self._mappings = mappings

    async def analyze(self, graph: ArchitectureGraph) -> list[Threat]:
        """Apply STRIDE rules to components and data flows."""
        mappings = self._mappings or StrideMappings.from_file(DEFAULT_STRIDE_MAPPINGS_PATH)
        component_by_id = {component.id: component for component in graph.components}
        boundary_by_component = self._build_boundary_index(graph.trust_boundaries)

        threats: list[Threat] = []

        for component in graph.components:
            for mapping in mappings.get_component_threats(component.type):
                threats.append(
                    self._build_component_threat(
                        component_id=component.id,
                        component_type=component.type,
                        mapping=mapping,
                    )
                )

        for flow in graph.data_flows:
            if flow.source_id not in component_by_id or flow.target_id not in component_by_id:
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
            component_id=component_id,
            component_type=component_type,
            description=cls._description_with_justification(mapping),
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
        if crosses_trust_boundary:
            description = f"{description} Cruza trust boundary."

        return Threat(
            id=cls._data_flow_threat_id(flow, mapping.category),
            category=mapping.category,
            component_id=flow_id,
            component_type=DATA_FLOW_COMPONENT_TYPE,
            description=description,
            severity=calculate_severity(
                DATA_FLOW_COMPONENT_TYPE,
                mapping.category,
                crosses_trust_boundary=crosses_trust_boundary,
            ),
            affected_data_flows=[flow_id],
        )

    @staticmethod
    def _description_with_justification(mapping: MappingThreat) -> str:
        if not mapping.justification:
            return mapping.description
        return f"{mapping.description} Justificativa: {mapping.justification}"

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
            if current is None or severity_sort_rank(threat.severity) < severity_sort_rank(
                current.severity
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
