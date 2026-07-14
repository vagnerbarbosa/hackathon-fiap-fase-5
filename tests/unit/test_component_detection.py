"""Testes para ComponentDetectionService."""

import pytest
from pathlib import Path
from uuid import UUID

from src.services.component_detection import ComponentDetectionService
from src.domain.models import ArchitectureGraph, DetectedComponent


class TestComponentDetectionService:
    """Testes para operações do ComponentDetectionService."""

    @pytest.fixture
    def service(self):
        """Cria uma instância do serviço em modo mock."""
        return ComponentDetectionService(model_path=None)

    async def test_detect_mock_mode(self, service, tmp_path):
        """Deve detectar componentes em modo mock."""
        # Cria um arquivo de imagem dummy
        image_path = tmp_path / "test.png"
        image_path.write_bytes(b"fake image content")

        result = await service.detect(image_path)

        assert isinstance(result, ArchitectureGraph)
        assert len(result.components) == 3
        assert len(result.data_flows) == 2
        assert len(result.trust_boundaries) == 3

    async def test_detect_components_types(self, service, tmp_path):
        """Deve detectar componentes user, api e database."""
        image_path = tmp_path / "test.png"
        image_path.write_bytes(b"fake image content")

        result = await service.detect(image_path)

        types = [c.type for c in result.components]
        assert "user" in types
        assert "api" in types
        assert "database" in types

    async def test_detect_component_structure(self, service, tmp_path):
        """Deve retornar componentes com estrutura válida."""
        image_path = tmp_path / "test.png"
        image_path.write_bytes(b"fake image content")

        result = await service.detect(image_path)

        for component in result.components:
            # Verifica formato UUID
            UUID(component.id)  # Não deve lançar exceção

            # Verifica range de confiança
            assert 0.0 <= component.confidence <= 1.0
            assert component.confidence >= 0.25

            # Verifica bounding box
            assert component.bbox.x_min < component.bbox.x_max
            assert component.bbox.y_min < component.bbox.y_max

            # Verifica ponto central
            assert component.center.x == (component.bbox.x_min + component.bbox.x_max) // 2
            assert component.center.y == (component.bbox.y_min + component.bbox.y_max) // 2

    async def test_detect_data_flows(self, service, tmp_path):
        """Deve inferir fluxos de dados entre componentes."""
        image_path = tmp_path / "test.png"
        image_path.write_bytes(b"fake image content")

        result = await service.detect(image_path)

        assert len(result.data_flows) > 0

        for flow in result.data_flows:
            # Verifica se o fluxo tem source e target válidos
            assert flow.source_id in [c.id for c in result.components]
            assert flow.target_id in [c.id for c in result.components]
            assert flow.direction in ["unidirectional", "bidirectional"]
            assert flow.inferred is True

    async def test_detect_trust_boundaries(self, service, tmp_path):
        """Deve atribuir componentes a trust boundaries."""
        image_path = tmp_path / "test.png"
        image_path.write_bytes(b"fake image content")

        result = await service.detect(image_path)

        # Todos os componentes devem estar em algum trust boundary
        all_boundary_components = []
        for boundary in result.trust_boundaries:
            all_boundary_components.extend(boundary)

        component_ids = [c.id for c in result.components]
        for comp_id in component_ids:
            assert comp_id in all_boundary_components

    async def test_detect_file_not_found(self, service):
        """Deve lançar FileNotFoundError para arquivo inexistente."""
        with pytest.raises(FileNotFoundError):
            await service.detect("/non/existent/file.png")

    def test_is_mock_mode(self, service):
        """Deve reportar modo mock quando nenhum modelo está carregado."""
        assert service.is_mock_mode() is True

    def test_service_initializes_without_model(self):
        """Deve inicializar sem um arquivo de modelo."""
        service = ComponentDetectionService(model_path="/non/existent/model.pt")
        assert service.model is None
        assert service.is_mock_mode() is True

    def test_service_with_invalid_model_path(self):
        """Deve tratar caminho de modelo inválido com graça."""
        service = ComponentDetectionService(model_path="/invalid/path.pt")
        assert service.is_mock_mode() is True

    async def test_detect_returns_architecture_graph(self, service, tmp_path):
        """Deve retornar tipo ArchitectureGraph."""
        image_path = tmp_path / "test.png"
        image_path.write_bytes(b"fake image content")

        result = await service.detect(image_path)

        assert isinstance(result, ArchitectureGraph)
        assert hasattr(result, 'components')
        assert hasattr(result, 'data_flows')
        assert hasattr(result, 'trust_boundaries')
