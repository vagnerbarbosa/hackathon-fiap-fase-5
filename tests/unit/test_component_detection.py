"""Testes para ComponentDetectionService."""

import pytest
from pathlib import Path
from uuid import UUID
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from src.services.component_detection import (
    ComponentDetectionService,
    LowConfidenceError,
    ModelNotLoadedError,
)
from src.domain.models import ArchitectureGraph, DetectedComponent


class TestComponentDetectionService:
    """Testes para operações do ComponentDetectionService."""

    @pytest.fixture
    def mock_onnx_session(self):
        """Cria um mock da sessão ONNX."""
        mock_session = MagicMock()
        # Simula output do ONNX: [batch, features, num_anchors]
        # 34 features = 4(box) + 1(conf) + 29(classes)
        # 8400 âncoras
        mock_output = np.random.rand(1, 34, 8400).astype(np.float32)
        # Seta confianças altas para algumas detecções
        mock_output[0, 4, :5] = 0.9  # 5 detecções com confiança 0.9
        mock_session.run.return_value = [mock_output]

        mock_input = MagicMock()
        mock_input.name = "input"
        mock_session.get_inputs.return_value = [mock_input]

        return mock_session

    @pytest.fixture
    def create_service_with_mock(self, mock_onnx_session, tmp_path):
        """Factory para criar serviço com modelo mock."""
        def _create_service():
            # Cria arquivo dummy para o modelo
            model_path = tmp_path / "model.onnx"
            model_path.write_bytes(b"fake onnx model")

            with patch('onnxruntime.InferenceSession', return_value=mock_onnx_session):
                service = ComponentDetectionService(model_path=str(model_path))
                return service
        return _create_service

    def test_service_raises_error_when_model_not_found(self, tmp_path):
        """Deve lançar ModelNotLoadedError quando modelo não existe."""
        with pytest.raises(ModelNotLoadedError) as exc_info:
            ComponentDetectionService(model_path=str(tmp_path / "nonexistent.onnx"))

        assert "não encontrado" in str(exc_info.value).lower()

    def test_service_raises_error_when_model_path_none(self):
        """Deve lançar ModelNotLoadedError quando path é None."""
        with pytest.raises(ModelNotLoadedError) as exc_info:
            ComponentDetectionService(model_path=None)

        assert "não configurado" in str(exc_info.value).lower()

    async def test_detect_file_not_found(self, create_service_with_mock, tmp_path):
        """Deve lançar FileNotFoundError para arquivo inexistente."""
        service = create_service_with_mock()

        with pytest.raises(FileNotFoundError):
            await service.detect("/non/existent/file.png")

    async def test_detect_low_confidence(self, tmp_path):
        """Deve lançar LowConfidenceError quando confiança é baixa."""
        # Cria mock com confianças muito baixas
        mock_session = MagicMock()
        mock_output = np.random.rand(1, 34, 8400).astype(np.float32) * 0.1  # Confianças < 0.1
        mock_session.run.return_value = [mock_output]
        mock_input = MagicMock()
        mock_input.name = "input"
        mock_session.get_inputs.return_value = [mock_input]

        # Cria arquivo dummy para o modelo
        model_path = tmp_path / "model.onnx"
        model_path.write_bytes(b"fake onnx model")

        with patch('onnxruntime.InferenceSession', return_value=mock_session):
            service = ComponentDetectionService(model_path=str(model_path))

            # Cria uma imagem dummy válida
            image_path = tmp_path / "test.png"
            from PIL import Image
            img = Image.new('RGB', (100, 100), color='white')
            img.save(image_path)

            with pytest.raises(LowConfidenceError) as exc_info:
                await service.detect(image_path)

            assert "baixa confiança" in str(exc_info.value).lower() or \
                   "não foi possível detectar" in str(exc_info.value).lower()

    def test_default_confidence_threshold(self):
        """Deve ter threshold padrão de 0.3."""
        assert ComponentDetectionService.DEFAULT_CONFIDENCE_THRESHOLD == 0.3

    def test_service_initializes_with_custom_threshold(self, tmp_path):
        """Deve aceitar threshold personalizado."""
        # Cria arquivo dummy
        model_path = tmp_path / "model.onnx"
        model_path.write_bytes(b"fake onnx model")

        mock_session = MagicMock()
        with patch('onnxruntime.InferenceSession', return_value=mock_session):
            service = ComponentDetectionService(
                model_path=str(model_path),
                confidence_threshold=0.5
            )
            assert service.confidence_threshold == 0.5

    async def test_detect_raises_model_error_when_no_model(self):
        """Deve lançar erro quando serviço é criado sem modelo válido."""
        # Tenta criar serviço sem modelo - deve falhar na inicialização
        with pytest.raises(ModelNotLoadedError):
            service = ComponentDetectionService(model_path=None)

    def test_low_confidence_error_has_message(self):
        """LowConfidenceError deve ter mensagem acessível."""
        error = LowConfidenceError("Mensagem de teste")
        assert error.message == "Mensagem de teste"
        assert str(error) == "Mensagem de teste"

    def test_model_not_loaded_error_has_message(self):
        """ModelNotLoadedError deve ter mensagem acessível."""
        error = ModelNotLoadedError("Modelo não encontrado")
        assert error.message == "Modelo não encontrado"
        assert str(error) == "Modelo não encontrado"

    async def test_detect_successful_with_mock(self, create_service_with_mock, tmp_path):
        """Deve detectar componentes quando confiança é alta."""
        service = create_service_with_mock()

        # Cria uma imagem válida
        image_path = tmp_path / "test.png"
        from PIL import Image
        img = Image.new('RGB', (640, 480), color='white')
        img.save(image_path)

        # Deve retornar ArchitectureGraph
        result = await service.detect(image_path)
        assert isinstance(result, ArchitectureGraph)
        assert len(result.components) > 0
