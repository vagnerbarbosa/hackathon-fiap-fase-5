"""Component Detection Service.

Orchestrates the full detection pipeline:
1. Check cache
2. Preprocess image
3. Run YOLO inference
4. Analyze relationships
5. Cache result
"""

import logging
from pathlib import Path
from typing import Union
from uuid import uuid4

from src.core.config import settings
from src.domain.models import (
    ArchitectureGraph,
    BoundingBox,
    DataFlow,
    DetectedComponent,
    Point,
)
from src.infrastructure.cache.detection_cache import DetectionCache
from src.infrastructure.ml.yolo_model import YOLOModel
from src.services.image_preprocessor import ImagePreprocessor
from src.services.relationship_analyzer import RelationshipAnalyzer

logger = logging.getLogger(__name__)


class ComponentDetectionService:
    """Service for detecting architectural components in images.

    Coordinates the full detection pipeline including preprocessing,
    model inference, relationship analysis, and caching.

    Usage:
        >>> service = ComponentDetectionService()
        >>> graph = await service.detect("diagram.png")
        >>> print(f"Found {len(graph.components)} components")

    Attributes:
        model: YOLO model wrapper (supports .pt and .onnx).
        preprocessor: Image preprocessing pipeline.
        analyzer: Relationship analyzer for flows and boundaries.
        cache: Redis cache for detection results.
    """

    def __init__(
        self,
        model_path: str = "models/best.pt",
        confidence_threshold: float = 0.25,
    ):
        """Initialize detection service.

        Args:
            model_path: Path to YOLO model file.
            confidence_threshold: Minimum confidence for detections.
        """
        self.model = YOLOModel(model_path)
        self.preprocessor = ImagePreprocessor(target_size=640)
        self.analyzer = RelationshipAnalyzer(
            proximity_threshold=150.0,
            alignment_tolerance=50.0,
        )
        self.cache = DetectionCache()
        self.confidence_threshold = confidence_threshold

        logger.info(
            f"Initialized ComponentDetectionService",
            extra={
                "model_path": str(model_path),
                "using_stub": self.model.is_stub,
                "confidence_threshold": confidence_threshold,
            },
        )

    async def detect(self, image_path: Union[str, Path]) -> ArchitectureGraph:
        """Detect components in image.

        Full pipeline:
        1. Check cache
        2. Load and preprocess image
        3. Run YOLO inference
        4. Convert to domain models
        5. Analyze relationships
        6. Cache result

        Args:
            image_path: Path to image file (PNG/JPG/JPEG).

        Returns:
            ArchitectureGraph with components, flows, and boundaries.

        Raises:
            FileNotFoundError: If image file not found.
            NoComponentsDetectedError: If no components detected.
        """
        image_path = Path(image_path)

        # Step 1: Check cache
        cached = await self.cache.get(image_path)
        if cached:
            logger.info(f"Returning cached result for {image_path.name}")
            return cached

        # Step 2: Preprocess
        logger.debug(f"Preprocessing {image_path.name}")
        preprocessed = self.preprocessor.preprocess(image_path)

        # Step 3: Run inference
        logger.info(f"Running inference on {image_path.name}")
        detections = self.model.predict(
            image_path,
            conf=self.confidence_threshold,
        )

        # Step 4: Convert to domain models
        components = self._convert_detections(detections)

        if not components:
            raise NoComponentsDetectedError(
                f"Nenhum componente detectado em {image_path.name}. "
                "Verifique se o diagrama está legível."
            )

        logger.info(f"Detected {len(components)} components in {image_path.name}")

        # Step 5: Analyze relationships
        logger.debug("Analyzing relationships")
        data_flows = self.analyzer.infer_data_flows(components)
        trust_boundaries = self.analyzer.infer_trust_boundaries(components)

        # Build result
        graph = ArchitectureGraph(
            components=components,
            data_flows=data_flows,
            trust_boundaries=trust_boundaries,
        )

        # Step 6: Cache result
        await self.cache.set(image_path, graph)

        return graph

    def _convert_detections(self, detections: list) -> list[DetectedComponent]:
        """Convert YOLO detections to domain models.

        Args:
            detections: List of DetectionResult from YOLO.

        Returns:
            List of DetectedComponent with generated IDs.
        """
        components = []

        for det in detections:
            component = DetectedComponent(
                id=str(uuid4()),
                type=det.class_name,
                confidence=det.confidence,
                bbox=BoundingBox(
                    x_min=int(det.bbox[0]),
                    y_min=int(det.bbox[1]),
                    x_max=int(det.bbox[2]),
                    y_max=int(det.bbox[3]),
                ),
                center=Point(
                    x=int((det.bbox[0] + det.bbox[2]) / 2),
                    y=int((det.bbox[1] + det.bbox[3]) / 2),
                ),
            )
            components.append(component)

        return components

    @property
    def is_using_stub(self) -> bool:
        """Check if using stub model (model not trained yet)."""
        return self.model.is_stub


class NoComponentsDetectedError(Exception):
    """Raised when no components are detected in image."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Convert error to API response format."""
        return {
            "error": "NO_COMPONENTS_DETECTED",
            "message": self.message,
            "supported_types": [
                "user",
                "web_server",
                "api",
                "database",
                "queue",
                "cache",
                "external_service",
                "mobile_app",
                "container",
                "storage",
            ],
        }
