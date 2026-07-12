"""Testes unitários para ComponentDetectionService.

Testes usam mocks para evitar carregar pesos reais do modelo YOLO.
"""

from pathlib import Path
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.core.circuit_breaker import CircuitBreakerOpen
from src.domain.models import ArchitectureGraph, BoundingBox, DetectedComponent, Point
from src.services.component_detector import (
    ComponentDetectionService,
    NoComponentsDetectedError,
)
from src.infrastructure.ml.yolo_model import DetectionResult


class TestComponentDetectionService:
    """Testes para ComponentDetectionService."""

    @pytest.fixture
    def service(self, tmp_path):
        """Cria instância do service com storage temporário."""
        # Service usará YOLOStub já que arquivo de modelo não existe
        return ComponentDetectionService(
            model_path=str(tmp_path / "nonexistent.pt"),
            confidence_threshold=0.25,
        )

    @pytest.fixture
    def mock_detections(self):
        """Cria resultados de detecção mockados."""
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
        """Service deve usar stub quando arquivo de modelo não existe."""
        assert service.is_using_stub is True

    def test_convert_detections_creates_components(self, service, mock_detections):
        """Converte detecções YOLO para componentes de domínio."""
        components = service._convert_detections(mock_detections)

        assert len(components) == 3
        assert all(isinstance(c, DetectedComponent) for c in components)
        assert components[0].type == "user"
        assert components[1].type == "api"
        assert components[2].type == "database"

    def test_convert_detections_calculates_centers(self, service, mock_detections):
        """Conversão deve calcular pontos centrais a partir de bboxes."""
        components = service._convert_detections(mock_detections)

        # Primeiro componente: bbox [10, 50, 60, 100]
        # Centro deve ser (35, 75)
        assert components[0].center.x == 35
        assert components[0].center.y == 75

        # Segundo componente: bbox [200, 50, 300, 120]
        # Centro deve ser (250, 85)
        assert components[1].center.x == 250
        assert components[1].center.y == 85

    def test_convert_detections_generates_uuids(self, service, mock_detections):
        """Conversão deve gerar UUIDs únicos para cada componente."""
        components = service._convert_detections(mock_detections)

        ids = [c.id for c in components]
        assert len(ids) == len(set(ids))  # Todos únicos

    def test_convert_empty_detections(self, service):
        """Converter detecções vazias deve retornar lista vazia."""
        components = service._convert_detections([])
        assert components == []

    @pytest.mark.asyncio
    async def test_detect_returns_architecture_graph(self, service, tmp_path):
        """Detect deve retornar ArchitectureGraph com todos os campos."""
        # Cria arquivo de imagem dummy
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
        """Detect deve filtrar componentes abaixo do threshold de confiança."""
        from PIL import Image
        img = Image.new("RGB", (640, 480), color="white")
        test_path = tmp_path / "test.png"
        img.save(test_path)

        # Usa threshold de confiança alto
        service.confidence_threshold = 0.90
        graph = await service.detect(test_path)

        # Deve retornar apenas componentes com confiança >= 0.90
        for comp in graph.components:
            assert comp.confidence >= 0.90

    @pytest.mark.asyncio
    async def test_detect_caches_results(self, service, tmp_path):
        """Detect deve cachear resultados para mesma imagem."""
        from PIL import Image
        img = Image.new("RGB", (640, 480), color="white")
        test_path = tmp_path / "test.png"
        img.save(test_path)

        # Primeira detecção
        graph1 = await service.detect(test_path)

        # Segunda detecção deve usar cache
        graph2 = await service.detect(test_path)

        # Resultados devem ser idênticos
        assert len(graph1.components) == len(graph2.components)


class TestNoComponentsDetectedError:
    """Testes para NoComponentsDetectedError."""

    def test_error_message(self):
        """Erro deve conter mensagem útil."""
        error = NoComponentsDetectedError("No components found")
        assert "No components found" in error.message

    def test_error_to_dict(self):
        """Erro deve converter para formato de resposta da API."""
        error = NoComponentsDetectedError("Test message")
        result = error.to_dict()

        assert result["error"] == "NO_COMPONENTS_DETECTED"
        assert "Test message" in result["message"]
        assert "supported_types" in result
        assert isinstance(result["supported_types"], list)
        assert "user" in result["supported_types"]
        assert "database" in result["supported_types"]


class TestDetectionResult:
    """Testes para data class DetectionResult."""

    def test_detection_result_creation(self):
        """Cria DetectionResult com todos os campos."""
        result = DetectionResult(
            class_name="api",
            confidence=0.95,
            bbox=[100.0, 100.0, 200.0, 200.0],
        )

        assert result.class_name == "api"
        assert result.confidence == 0.95
        assert result.bbox == [100.0, 100.0, 200.0, 200.0]


class TestCircuitBreakerIntegration:
    """Testes para integração com Circuit Breaker."""

    @pytest.fixture
    def service(self, tmp_path):
        """Cria service com circuit breaker."""
        return ComponentDetectionService(
            model_path=str(tmp_path / "nonexistent.pt"),
            confidence_threshold=0.25,
        )

    @pytest.mark.asyncio
    async def test_circuit_breaker_exists(self, service):
        """Service deve ter circuit breaker."""
        assert hasattr(service, '_circuit_breaker')
        assert service._circuit_breaker.name == "yolo_inference"

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self, service, tmp_path):
        """Circuito deve abrir após múltiplas falhas."""
        from PIL import Image
        img = Image.new("RGB", (640, 480), color="white")
        test_path = tmp_path / "test.png"
        img.save(test_path)

        # Mock do modelo para sempre falhar
        service.model.predict = MagicMock(side_effect=RuntimeError("Model failed"))

        # 3 falhas para abrir circuito
        for _ in range(3):
            with pytest.raises(Exception):
                await service.detect(test_path)

        assert service._circuit_breaker.state.value == "open"

    @pytest.mark.asyncio
    async def test_circuit_breaker_allows_success(self, service):
        """Circuito deve permitir chamadas bem-sucedidas."""
        assert service._circuit_breaker.state.value == "closed"


class TestCacheInjection:
    """Testes para injeção de dependência de cache."""

    @pytest.fixture
    def service(self, tmp_path):
        """Cria service com cache padrão."""
        return ComponentDetectionService(
            model_path=str(tmp_path / "nonexistent.pt"),
            confidence_threshold=0.25,
        )

    @pytest.mark.asyncio
    async def test_uses_cache_factory_by_default(self, service):
        """Service deve usar CacheFactory por padrão."""
        from src.infrastructure.cache.cache_factory import CacheFactory
        assert service.cache is not None

    @pytest.mark.asyncio
    async def test_allows_custom_cache(self, tmp_path):
        """Service deve aceitar cache customizado."""
        from src.infrastructure.cache.in_memory_cache import InMemoryCache
        custom_cache = InMemoryCache()

        service = ComponentDetectionService(
            model_path=str(tmp_path / "nonexistent.pt"),
            confidence_threshold=0.25,
            cache=custom_cache,
        )

        assert service.cache is custom_cache


class TestRetryIntegration:
    """Testes para integração com Retry."""

    @pytest.mark.asyncio
    async def test_run_inference_with_circuit_breaker_exists(self, tmp_path):
        """Service deve ter inferência wrapada com retry."""
        service = ComponentDetectionService(
            model_path=str(tmp_path / "nonexistent.pt"),
            confidence_threshold=0.25,
        )

        assert hasattr(service, '_run_inference_with_circuit_breaker')
        assert hasattr(service, '_run_inference_sync')
