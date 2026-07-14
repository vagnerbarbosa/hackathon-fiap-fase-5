"""Mock ArchitectureGraph for Spec 004 and 006 testing."""

from uuid import uuid4

from src.domain.models import (
    ArchitectureGraph,
    BoundingBox,
    DataFlow,
    DetectedComponent,
    Point,
)

# Create components with fixed IDs for consistent testing
user_id = str(uuid4())
api_id = str(uuid4())
database_id = str(uuid4())

# Create mock graph with 3 components: user, api, database
fake_graph = ArchitectureGraph(
    components=[
        DetectedComponent(
            id=user_id,
            type="user",
            confidence=0.95,
            bbox=BoundingBox(x_min=10, y_min=50, x_max=60, y_max=100),
            center=Point(x=35, y=75),
        ),
        DetectedComponent(
            id=api_id,
            type="api",
            confidence=0.91,
            bbox=BoundingBox(x_min=200, y_min=50, x_max=300, y_max=120),
            center=Point(x=250, y=85),
        ),
        DetectedComponent(
            id=database_id,
            type="database",
            confidence=0.88,
            bbox=BoundingBox(x_min=400, y_min=60, x_max=480, y_max=110),
            center=Point(x=440, y=85),
        ),
    ],
    data_flows=[
        DataFlow(
            source_id=user_id,
            target_id=api_id,
            direction="unidirectional",
            inferred=True,
        ),
        DataFlow(
            source_id=api_id,
            target_id=database_id,
            direction="unidirectional",
            inferred=True,
        ),
    ],
    trust_boundaries=[[user_id], [api_id, database_id]],
)

if __name__ == "__main__":
    print(f"Created ArchitectureGraph with {len(fake_graph.components)} components")
    print(f"Data flows: {len(fake_graph.data_flows)}")
    print(f"Trust boundaries: {len(fake_graph.trust_boundaries)}")
