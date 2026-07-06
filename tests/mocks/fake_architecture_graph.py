"""Mock ArchitectureGraph for Spec 004 and 006 testing."""

from uuid import uuid4

from domain.models import (
    ArchitectureGraph,
    BoundingBox,
    DataFlow,
    DetectedComponent,
    Point,
)

# Create mock graph with 3 components: user, api, database
fake_graph = ArchitectureGraph(
    components=[
        DetectedComponent(
            id=str(uuid4()),
            type="user",
            confidence=0.95,
            bbox=BoundingBox(x_min=10, y_min=50, x_max=60, y_max=100),
            center=Point(x=35, y=75),
        ),
        DetectedComponent(
            id=str(uuid4()),
            type="api",
            confidence=0.91,
            bbox=BoundingBox(x_min=200, y_min=50, x_max=300, y_max=120),
            center=Point(x=250, y=85),
        ),
        DetectedComponent(
            id=str(uuid4()),
            type="database",
            confidence=0.88,
            bbox=BoundingBox(x_min=400, y_min=60, x_max=480, y_max=110),
            center=Point(x=440, y=85),
        ),
    ],
    data_flows=[
        DataFlow(
            source_id="comp-1",
            target_id="comp-2",
            direction="unidirectional",
            inferred=True,
        ),
        DataFlow(
            source_id="comp-2",
            target_id="comp-3",
            direction="unidirectional",
            inferred=True,
        ),
    ],
    trust_boundaries=[["comp-1"], ["comp-2", "comp-3"]],
)

if __name__ == "__main__":
    print(f"Created ArchitectureGraph with {len(fake_graph.components)} components")
    print(f"Data flows: {len(fake_graph.data_flows)}")
    print(f"Trust boundaries: {len(fake_graph.trust_boundaries)}")
