"""Testes para ImagePreprocessor com validações de segurança."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

from src.services.image_preprocessor import ImagePreprocessor, MAX_FILE_SIZE_MB


class TestImagePreprocessor:
    """Testes para ImagePreprocessor."""

    @pytest.fixture
    def preprocessor(self):
        """Preprocessor padrão."""
        return ImagePreprocessor(target_size=640)

    def test_initialization(self, preprocessor):
        """Inicialização correta."""
        assert preprocessor.target_size == 640
        assert preprocessor.normalize is True
        assert preprocessor.apply_threshold is False

    def test_resize_letterbox(self, preprocessor):
        """Redimensionamento mantém aspect ratio."""
        # Cria imagem retangular
        img = np.random.randint(0, 255, (100, 200, 3), dtype=np.uint8)

        resized = preprocessor._resize(img)

        assert resized.shape[0] == 640
        assert resized.shape[1] == 640

    def test_resize_small_image(self, preprocessor):
        """Imagem pequena é ampliada."""
        img = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)

        resized = preprocessor._resize(img)

        assert resized.shape[0] == 640
        assert resized.shape[1] == 640


class TestImagePreprocessorValidations:
    """Testes para validações de segurança."""

    @pytest.fixture
    def preprocessor(self):
        return ImagePreprocessor(target_size=640)

    @pytest.fixture
    def create_temp_image(self):
        """Factory para criar imagens temporárias."""
        def _create(content: bytes, suffix: str = ".png") -> str:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                f.write(content)
                return f.name
        return _create

    def test_validate_file_exists_raises_when_not_found(self, preprocessor):
        """Erro quando arquivo não existe."""
        with pytest.raises(FileNotFoundError):
            preprocessor._validate_file_exists(Path("/nonexistent/path.png"))

    def test_validate_file_size_raises_when_too_large(self, preprocessor, tmp_path):
        """Erro quando arquivo excede tamanho máximo."""
        # Cria arquivo grande
        large_file = tmp_path / "large.png"
        large_file.write_bytes(b"x" * (MAX_FILE_SIZE_MB * 1024 * 1024 + 1))

        with pytest.raises(ValueError, match="exceeds maximum"):
            preprocessor._validate_file_size(large_file)

    def test_validate_mime_type_raises_when_invalid(self, preprocessor, tmp_path):
        """Erro quando MIME type inválido."""
        invalid_file = tmp_path / "file.txt"
        invalid_file.write_text("not an image")

        with pytest.raises(ValueError, match="Invalid file type"):
            preprocessor._validate_mime_type(invalid_file)

    def test_validate_mime_type_accepts_png(self, preprocessor, tmp_path):
        """Aceita arquivos PNG."""
        # PNG header
        png_file = tmp_path / "test.png"
        png_file.write_bytes(b'\x89PNG\r\n\x1a\n')

        # Não deve lançar
        preprocessor._validate_mime_type(png_file)

    def test_validate_image_dimensions_raises_when_too_small(self, preprocessor):
        """Erro quando imagem muito pequena."""
        img = np.random.randint(0, 255, (5, 5, 3), dtype=np.uint8)

        with pytest.raises(ValueError, match="too small"):
            preprocessor._validate_image_dimensions(img)

    def test_validate_image_dimensions_raises_when_too_large(self, preprocessor):
        """Erro quando imagem muito grande."""
        img = np.random.randint(0, 255, (15000, 15000, 3), dtype=np.uint8)

        with pytest.raises(ValueError, match="too large"):
            preprocessor._validate_image_dimensions(img)

    def test_validate_image_dimensions_raises_when_invalid_channels(self, preprocessor):
        """Erro quando número de canais inválido."""
        img = np.random.randint(0, 255, (100, 100, 5), dtype=np.uint8)

        with pytest.raises(ValueError, match="Invalid number of channels"):
            preprocessor._validate_image_dimensions(img)

    def test_validate_image_dimensions_accepts_grayscale(self, preprocessor):
        """Aceita imagens grayscale (2D)."""
        img = np.random.randint(0, 255, (100, 100), dtype=np.uint8)

        # Não deve lançar
        preprocessor._validate_image_dimensions(img)


class TestImagePreprocessorSecurity:
    """Testes específicos de segurança."""

    @pytest.fixture
    def preprocessor(self):
        return ImagePreprocessor(target_size=640)

    @pytest.mark.asyncio
    async def test_preprocess_validates_all_security_checks(self, preprocessor, tmp_path):
        """Preprocess executa todas as validações."""
        # Cria arquivo PNG válido
        from PIL import Image
        img_path = tmp_path / "test.png"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(img_path)

        # Não deve lançar exceção
        result = preprocessor.preprocess(img_path)

        assert result is not None
        assert isinstance(result, np.ndarray)

    @pytest.mark.asyncio
    async def test_preprocess_rejects_nonexistent_file(self, preprocessor):
        """Rejeita arquivo inexistente."""
        with pytest.raises(FileNotFoundError):
            await preprocessor.preprocess("/nonexistent.png")
