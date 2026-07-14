import asyncio
import json
import logging

import pytest

from src.core.stride_mappings import StrideMappings
from src.domain.models import (
    ArchitectureGraph,
    BoundingBox,
    DataFlow,
    DetectedComponent,
    Point,
    Severity,
    Threat,
)
from src.services.stride_engine import StrideEngine


def component(component_id: str, component_type: str) -> DetectedComponent:
    return DetectedComponent(
        id=component_id,
        type=component_type,
        confidence=0.95,
        bbox=BoundingBox(x_min=0, y_min=0, x_max=10, y_max=10),
        center=Point(x=5, y=5),
    )


@pytest.fixture()
def engine() -> StrideEngine:
    return StrideEngine(StrideMappings.from_file())


def analyze(engine: StrideEngine, graph: ArchitectureGraph) -> list[Threat]:
    return asyncio.run(engine.analyze(graph))


def test_database_generates_expected_categories_without_spoofing(
    engine: StrideEngine,
) -> None:
    graph = ArchitectureGraph(
        components=[component("database-1", "database")],
        data_flows=[],
        trust_boundaries=[["database-1"]],
    )

    threats = analyze(engine, graph)
    categories = {threat.category for threat in threats}

    assert categories == {"T", "R", "I", "D", "E"}
    assert "S" not in categories


def test_api_generates_all_stride_categories(engine: StrideEngine) -> None:
    graph = ArchitectureGraph(
        components=[component("api-1", "api")],
        data_flows=[],
        trust_boundaries=[["api-1"]],
    )

    threats = analyze(engine, graph)

    assert {threat.category for threat in threats} == {"S", "T", "R", "I", "D", "E"}


def test_threats_include_category_name_and_justification(engine: StrideEngine) -> None:
    graph = ArchitectureGraph(
        components=[component("api-1", "api")],
        data_flows=[],
        trust_boundaries=[["api-1"]],
    )

    threats = analyze(engine, graph)
    spoofing = next(threat for threat in threats if threat.category == "S")

    assert spoofing.category_name == "Spoofing"
    assert spoofing.justification
    assert "token" in spoofing.description.lower()


def test_data_flow_generates_threats_with_affected_flow(
    engine: StrideEngine,
) -> None:
    graph = ArchitectureGraph(
        components=[
            component("user-1", "user"),
            component("api-1", "api"),
        ],
        data_flows=[
            DataFlow(
                source_id="user-1",
                target_id="api-1",
                direction="unidirectional",
                inferred=True,
            )
        ],
        trust_boundaries=[["user-1", "api-1"]],
    )

    threats = analyze(engine, graph)
    flow_threats = [threat for threat in threats if threat.component_type == "data_flow"]

    assert {threat.category for threat in flow_threats} == {"T", "I", "D"}
    assert all(
        threat.affected_data_flows == ["flow:user-1:api-1:unidirectional"]
        for threat in flow_threats
    )


def test_trust_boundary_crossing_increases_flow_severity(
    engine: StrideEngine,
) -> None:
    graph = ArchitectureGraph(
        components=[
            component("user-1", "user"),
            component("api-1", "api"),
        ],
        data_flows=[
            DataFlow(
                source_id="user-1",
                target_id="api-1",
                direction="unidirectional",
                inferred=True,
            )
        ],
        trust_boundaries=[["user-1"], ["api-1"]],
    )

    threats = analyze(engine, graph)
    flow_threats = [threat for threat in threats if threat.component_type == "data_flow"]

    assert flow_threats
    assert {threat.category for threat in flow_threats} == {
        "S",
        "T",
        "R",
        "I",
        "D",
        "E",
    }
    assert all(
        threat.severity in {Severity.HIGH, Severity.CRITICAL}
        for threat in flow_threats
    )


def test_database_information_disclosure_is_critical(
    engine: StrideEngine,
) -> None:
    graph = ArchitectureGraph(
        components=[component("database-1", "database")],
        data_flows=[],
        trust_boundaries=[["database-1"]],
    )

    threats = analyze(engine, graph)
    database_i = next(threat for threat in threats if threat.category == "I")

    assert database_i.severity == Severity.CRITICAL


def test_cache_denial_of_service_is_low(engine: StrideEngine) -> None:
    graph = ArchitectureGraph(
        components=[component("cache-1", "cache")],
        data_flows=[],
        trust_boundaries=[["cache-1"]],
    )

    threats = analyze(engine, graph)
    cache_d = next(threat for threat in threats if threat.category == "D")

    assert cache_d.severity == Severity.LOW


def test_unknown_component_does_not_break_engine(
    engine: StrideEngine,
    caplog: pytest.LogCaptureFixture,
) -> None:
    graph = ArchitectureGraph(
        components=[component("custom-1", "custom_component")],
        data_flows=[],
        trust_boundaries=[["custom-1"]],
    )

    caplog.set_level(logging.WARNING, logger="src.services.stride_engine")

    assert analyze(engine, graph) == []
    payload = json.loads(caplog.records[0].message)
    assert payload["level"] == "warning"
    assert payload["module"] == "src.services.stride_engine"
    assert payload["message"] == "Unknown component type in STRIDE analysis."
    assert payload["component_id"] == "custom-1"
    assert payload["component_type"] == "custom_component"


def test_analysis_is_deterministic(engine: StrideEngine) -> None:
    graph = ArchitectureGraph(
        components=[
            component("user-1", "user"),
            component("api-1", "api"),
            component("database-1", "database"),
        ],
        data_flows=[
            DataFlow(
                source_id="user-1",
                target_id="api-1",
                direction="unidirectional",
                inferred=True,
            ),
            DataFlow(
                source_id="api-1",
                target_id="database-1",
                direction="unidirectional",
                inferred=True,
            ),
        ],
        trust_boundaries=[["user-1"], ["api-1", "database-1"]],
    )

    first = analyze(engine, graph)
    second = analyze(engine, graph)

    assert [threat.id for threat in first] == [threat.id for threat in second]
