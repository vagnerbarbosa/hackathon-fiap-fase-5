"""Unit tests for ComponentDetectionService.

Tests use mocks to avoid loading actual YOLO model weights.
"""

from pathlib import Path
from uuid import uuid4

import pytest
from src.domain.models import ArchitectureGraph, BoundingBox, DetectedComponent, Point
from src.services.component_detector import (
    ComponentDetectionService,
    NoComponentsDetectedError,
)
from src.infrastructure.ml.yolo_model import DetectionResult


class TestComponentDetectionService:
    """Tests for ComponentDetectionService."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create service instance with temporary storage."""
        # Service will use YOLOStub since no model file exists
        return ComponentDetectionService(
            model_path=str(tmp_path / "nonexistent.pt"),
            confidence_threshold=0.25,
        )

    @pytest.fixture
    def mock_detections(self):
        """Create mock detection results."""
        return [
            DetectionResult(
                class_name="user",
                confidence=0.95,
                bbox=[10.0, 50.0, 60.0, 100.0],
            ),
            DetectionResult(
                class_name="api",
                confidence=0.91,
                bbox=[200.0, 50.0, 300.0, 120.0],
            ),
            DetectionResult(
                class_name="database",
                confidence=0.88,
                bbox=[400.0, 60.0, 500.0, 140.0],
            ),
        ]

    def test_service_uses_stub_when_no_model(self, service):
        """Service should use stub when model file doesn't exist."""
        assert service.is_using_stub is True

    def test_convert_detections_creates_components(self, service, mock_detections):
        """Convert YOLO detections to domain components."""
        components = service._convert_detections(mock_detections)

        assert len(components) == 3
        assert all(isinstance(c, DetectedComponent) for c in components)
        assert components[0].type == "user"
        assert components[1].type == "api"
        assert components[2].type == "database"

    def test_convert_detections_calculates_centers(self, service, mock_detections):
        """Convert should calculate center points from bboxes."""
        components = service._convert_detections(mock_detections)

        # First component: bbox [10, 50, 60, 100]
        # Center should be (35, 75)
        assert components[0].center.x == 35
        assert components[0].center.y == 75

        # Second component: bbox [200, 50, 300, 120]
        # Center should be (250, 85)
        assert components[1].center.x == 250
        assert components[1].center.y == 85

    def test_convert_detections_generates_uuids(self, service, mock_detections):
        """Convert should generate unique UUIDs for each component."""
        components = service._convert_detections(mock_detections)

        ids = [c.id for c in components]
        assert len(ids) == len(set(ids))  # All unique

    def test_convert_empty_detections(self, service):
        """Convert empty detections should return empty list."""
        components = service._convert_detections([])
        assert components == []

    @pytest.mark.asyncio
    async def test_detect_returns_architecture_graph(self, service, tmp_path):
        """Detect should return ArchitectureGraph with all fields."""
        # Create a dummy image file
        from PIL import Image
        img = Image.new("RGB", (640, 480), color="white")
        test_path = tmp_path / "test.png"
        img.save(test_path)

        graph = await service.detect(test_path)

        assert isinstance(graph, ArchitectureGraph)
        assert len(graph.components) > 0
        assert isinstance(graph.data_flows, list)
        assert isinstance(graph.trust_boundaries, list)

    @pytest.mark.asyncio
    async def test_detect_filters_by_confidence(self, service, tmp_path):
        """Detect should filter components below confidence threshold."""
        from PIL import Image
        img = Image.new("RGB", (640, 480), color="white")
        test_path = tmp_path / "test.png"
        img.save(test_path)

        # Use high confidence threshold
        service.confidence_threshold = 0.90
        graph = await service.detect(test_path)

        # Should only return components with confidence >= 0.90
        for comp in graph.components:
            assert comp.confidence >= 0.90

    @pytest.mark.asyncio
    async def test_detect_caches_results(self, service, tmp_path):
        """Detect should cache results for same image."""
        from PIL import Image
        img = Image.new("RGB", (640, 480), color="white")
        test_path = tmp_path / "test.png"
        img.save(test_path)

        # First detection
        graph1 = await service.detect(test_path)

        # Second detection should use cache
        graph2 = await service.detect(test_path)

        # Results should be identical
        assert len(graph1.components) == len(graph2.components)


class TestNoComponentsDetectedError:
    """Tests for NoComponentsDetectedError."""

    def test_error_message(self):
        """Error should contain helpful message."""
        error = NoComponentsDetectedError("No components found")
        assert "No components found" in error.message

    def test_error_to_dict(self):
        """Error should convert to API response format."""
        error = NoComponentsDetectedError("Test message")
        result = error.to_dict()

        assert result["error"] == "NO_COMPONENTS_DETECTED"
        assert "Test message" in result["message"]
        assert "supported_types" in result
        assert isinstance(result["supported_types"], list)
        assert "user" in result["supported_types"]
        assert "database" in result["supported_types"]


class TestDetectionResult:
    """Tests for DetectionResult data class."""

    def test_detection_result_creation(self):
        """Create DetectionResult with all fields."""
        result = DetectionResult(
            class_name="api",
            confidence=0.95,
            bbox=[100.0, 100.0, 200.0, 200.0],
        )

        assert result.class_name == "api"
        assert result.confidence == 0.95
        assert result.bbox == [100.0, 100.0, 200.0, 200.0]
