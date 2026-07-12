"""Serviço de Detecção de Componentes.

Orquestra o pipeline completo de detecção:
1. Verifica cache
2. Pré-processa imagem
3. Executa inferência YOLO (com circuit breaker e retry)
4. Analisa relacionamentos
5. Armazena resultado em cache
"""

import logging
from pathlib import Path
from typing import Union
from uuid import uuid4

from src.core.circuit_breaker import CircuitBreaker, CircuitBreakerOpen
from src.core.config import settings
from src.core.retry import retry, RETRY_AI_SERVICE
from src.domain.models import (
    ArchitectureGraph,
    BoundingBox,
    DataFlow,
    DetectedComponent,
    Point,
)
from src.infrastructure.cache.cache_factory import CacheFactory
from src.infrastructure.cache.cache_interface import CacheInterface
from src.infrastructure.ml.yolo_model import YOLOModel
from src.services.image_preprocessor import ImagePreprocessor
from src.services.relationship_analyzer import RelationshipAnalyzer

logger = logging.getLogger(__name__)


class ComponentDetectionService:
    """Serviço para detecção de componentes arquiteturais em imagens.

    Coordena o pipeline completo de detecção incluindo pré-processamento,
    inferência do modelo, análise de relacionamentos e cache.

    Usage:
        >>> service = ComponentDetectionService()
        >>> graph = await service.detect("diagram.png")
        >>> print(f"Found {len(graph.components)} components")

    Attributes:
        model: Wrapper do modelo YOLO (suporta .pt e .onnx).
        preprocessor: Pipeline de pré-processamento de imagens.
        analyzer: Analisador de relacionamentos para flows e boundaries.
        cache: Cache Redis para resultados de detecção.
    """

    def __init__(
        self,
        model_path: str = "models/best.pt",
        confidence_threshold: float = 0.25,
        cache: CacheInterface = None,
    ):
        """Inicializa o serviço de detecção.

        Args:
            model_path: Caminho para o arquivo do modelo YOLO.
            confidence_threshold: Confiança mínima para detecções.
            cache: Instância de cache (usa CacheFactory se None).
        """
        self.model = YOLOModel(model_path)
        self.preprocessor = ImagePreprocessor(target_size=640)
        self.analyzer = RelationshipAnalyzer(
            proximity_threshold=150.0,
            alignment_tolerance=50.0,
        )
        # Usa injeção de dependência para cache (desacoplado)
        self.cache = cache or CacheFactory.create_cache()
        self.confidence_threshold = confidence_threshold

        # Circuit breaker para proteção contra falhas do modelo
        self._circuit_breaker = CircuitBreaker(
            name="yolo_inference",
            failure_threshold=3,
            recovery_timeout=30.0,
            expected_exception=(RuntimeError, ConnectionError, TimeoutError),
        )

        logger.info(
            f"Initialized ComponentDetectionService",
            extra={
                "model_path": str(model_path),
                "using_stub": self.model.is_stub,
                "confidence_threshold": confidence_threshold,
                "cache_type": type(self.cache).__name__,
            },
        )

    async def detect(self, image_path: Union[str, Path]) -> ArchitectureGraph:
        """Detecta componentes na imagem.

        Pipeline completo:
        1. Verifica cache
        2. Carrega e pré-processa imagem
        3. Executa inferência YOLO
        4. Converte para modelos de domínio
        5. Analisa relacionamentos
        6. Armazena em cache

        Args:
            image_path: Caminho para o arquivo de imagem (PNG/JPG/JPEG).

        Returns:
            ArchitectureGraph com componentes, flows e boundaries.

        Raises:
            FileNotFoundError: Se arquivo de imagem não encontrado.
            NoComponentsDetectedError: Se nenhum componente detectado.
        """
        image_path = Path(image_path)

        # Step 1: Check cache
        cached = await self.cache.get(image_path)
        if cached:
            logger.info(f"Returning cached result for {image_path.name}")
            return cached

        # Step 2: Preprocess (com validação rigorosa)
        logger.debug(f"Preprocessing {image_path.name}")
        try:
            preprocessed = self.preprocessor.preprocess(image_path)
        except ValueError as e:
            logger.error(f"Invalid image: {e}")
            raise

        # Step 3: Run inference (com circuit breaker e retry)
        logger.info(f"Running inference on {image_path.name}")
        try:
            detections = await retry(
                self._run_inference_with_circuit_breaker,
                image_path,
                config=RETRY_AI_SERVICE,
            )
        except Exception as e:
            logger.error(f"Inference failed after retries: {e}")
            # Se circuit breaker abriu, retorna erro amigável
            if isinstance(e, CircuitBreakerOpen):
                raise CircuitBreakerOpen(
                    "Serviço de IA temporariamente indisponível. "
                    "Tente novamente em alguns minutos."
                )
            raise

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
        """Converte detecções YOLO para modelos de domínio.

        Args:
            detections: Lista de DetectionResult do YOLO.

        Returns:
            Lista de DetectedComponent com IDs gerados.
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

    async def _run_inference_with_circuit_breaker(self, image_path: Path) -> list:
        """Executa inferência protegida por circuit breaker.

        Args:
            image_path: Caminho para a imagem.

        Returns:
            Lista de detecções do modelo.

        Raises:
            CircuitBreakerOpen: Se circuito está aberto.
            Exception: Falhas na inferência.
        """
        return await self._circuit_breaker.call(
            self._run_inference_sync,
            image_path,
        )

    def _run_inference_sync(self, image_path: Path) -> list:
        """Wrapper síncrono para inferência.

        Args:
            image_path: Caminho para a imagem.

        Returns:
            Lista de detecções.
        """
        return self.model.predict(
            image_path,
            conf=self.confidence_threshold,
        )

    @property
    def is_using_stub(self) -> bool:
        """Verifica se está usando modelo stub (modelo ainda não treinado)."""
        return self.model.is_stub


class NoComponentsDetectedError(Exception):
    """Lançado quando nenhum componente é detectado na imagem."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Converte erro para formato de resposta da API."""
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
