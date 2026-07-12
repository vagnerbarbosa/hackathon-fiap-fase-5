"""Stub/mock for YOLO model to enable parallel development.

This module provides a mock implementation of the Ultralytics YOLO interface,
allowing Spec 003 development without waiting for Spec 002 (model training).

When Lucas finishes Spec 002, replace YOLOStub with actual YOLO model.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional
from uuid import uuid4


@dataclass
class MockBox:
    """Mock YOLO detection box."""

    cls: str  # class name, e.g., "user", "api", "database"
    conf: float  # confidence 0.0-1.0
    xyxy: List[float]  # [x_min, y_min, x_max, y_max]

    @property
    def xywh(self) -> List[float]:
        """Convert xyxy to xywh (center x, center y, width, height)."""
        x_min, y_min, x_max, y_max = self.xyxy
        w = x_max - x_min
        h = y_max - y_min
        x_center = x_min + w / 2
        y_center = y_min + h / 2
        return [x_center, y_center, w, h]


@dataclass
class MockResult:
    """Mock YOLO result containing detections."""

    boxes: List[MockBox] = field(default_factory=list)

    def __iter__(self):
        """Allow iteration over boxes."""
        return iter(self.boxes)


class YOLOStub:
    """Stub implementation of Ultralytics YOLO model.

    Simulates a trained YOLOv11n model for architecture component detection.
    Returns mock detections without actually running inference.

    Usage:
        >>> from tests.mocks.yolo_stub import YOLOStub
        >>> model = YOLOStub("models/best.pt")
        >>> results = model.predict("image.jpg", conf=0.25)
        >>> for box in results[0].boxes:
        ...     print(f"{box.cls}: {box.conf:.2f}")
    """

    # Class-level model names mapping (label_id -> class_name)
    names = {
        0: "user",
        1: "web_server",
        2: "api",
        3: "database",
        4: "queue",
        5: "cache",
        6: "external_service",
        7: "mobile_app",
        8: "container",
        9: "storage",
    }

    def __init__(self, model_path: Optional[str] = None, task: Optional[str] = None):
        """Initialize stub (no actual model loading).

        Args:
            model_path: Ignored in stub (for compatibility).
            task: Ignored in stub (for compatibility).
        """
        self._model_path = model_path
        self._task = task or "detect"

    def predict(
        self,
        source: Any,
        conf: float = 0.25,
        iou: float = 0.45,
        imgsz: int = 640,
        **kwargs: Any,
    ) -> List[MockResult]:
        """Mock prediction returning simulated detections.

        Args:
            source: Image path or PIL/numpy image (ignored in stub).
            conf: Confidence threshold (filtered in mock).
            iou: IoU threshold for NMS (ignored in stub).
            imgsz: Input image size (ignored in stub).
            **kwargs: Additional arguments (ignored in stub).

        Returns:
            List[MockResult]: Simulated detection results.
        """
        # Simulate typical architecture diagram components
        mock_boxes = [
            MockBox(cls="user", conf=0.95, xyxy=[10.0, 50.0, 60.0, 100.0]),
            MockBox(cls="api", conf=0.91, xyxy=[200.0, 50.0, 300.0, 120.0]),
            MockBox(cls="database", conf=0.88, xyxy=[400.0, 60.0, 500.0, 140.0]),
            MockBox(cls="external_service", conf=0.72, xyxy=[600.0, 40.0, 680.0, 90.0]),
            MockBox(cls="cache", conf=0.65, xyxy=[350.0, 200.0, 420.0, 260.0]),
        ]

        # Filter by confidence threshold
        filtered_boxes = [b for b in mock_boxes if b.conf >= conf]

        return [MockResult(boxes=filtered_boxes)]

    def __call__(self, source: Any, **kwargs: Any) -> List[MockResult]:
        """Allow model(source) syntax."""
        return self.predict(source, **kwargs)


class YOLOWrapper:
    """Wrapper that tries real YOLO, falls back to stub."""

    def __init__(self, model_path: str = "models/best.pt"):
        """Initialize wrapper.

        Tries to load real YOLO model, falls back to stub if not available.

        Args:
            model_path: Path to model file (.pt or .onnx).
        """
        self.model_path = model_path
        self._model = None
        self._using_stub = False

        self._load_model()

    def _load_model(self) -> None:
        """Attempt to load model, fallback to stub."""
        try:
            from ultralytics import YOLO

            self._model = YOLO(self.model_path)
            self._using_stub = False
        except (ImportError, FileNotFoundError) as e:
            # Fallback to stub
            self._model = YOLOStub(self.model_path)
            self._using_stub = True
            print(f"[YOLOWrapper] Using stub (reason: {e})")

    @property
    def is_stub(self) -> bool:
        """Check if using stub implementation."""
        return self._using_stub

    @property
    def names(self) -> dict:
        """Get class names mapping."""
        return self._model.names

    def predict(self, *args: Any, **kwargs: Any) -> Any:
        """Run prediction (delegates to model or stub)."""
        return self._model.predict(*args, **kwargs)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Allow model(source) syntax."""
        return self._model(*args, **kwargs)


# Convenience instances for tests
stub_model = YOLOStub()
standard_mock_result = MockResult(
    boxes=[
        MockBox(cls="user", conf=0.95, xyxy=[10.0, 50.0, 60.0, 100.0]),
        MockBox(cls="api", conf=0.91, xyxy=[200.0, 50.0, 300.0, 120.0]),
        MockBox(cls="database", conf=0.88, xyxy=[400.0, 60.0, 500.0, 140.0]),
    ]
)
