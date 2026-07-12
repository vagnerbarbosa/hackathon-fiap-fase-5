"""Testes para LocalFileStorage."""

import pytest
from pathlib import Path

from src.infrastructure.storage import LocalFileStorage


class TestLocalFileStorage:
    """Testes para operações do LocalFileStorage."""

    @pytest.fixture
    def storage(self, tmp_path):
        """Cria instância de storage com diretório temporário."""
        return LocalFileStorage(base_path=str(tmp_path))

    async def test_save_file(self, storage, tmp_path):
        """Deve salvar arquivo e retornar caminho relativo."""
        content = b"test content"
        relative_path = await storage.save(content, "test.txt")

        assert relative_path is not None
        full_path = tmp_path / relative_path
        assert full_path.exists()
        assert full_path.read_bytes() == content

    async def test_save_file_without_filename(self, storage, tmp_path):
        """Deve gerar nome de arquivo se não fornecido."""
        content = b"test content"
        relative_path = await storage.save(content)

        assert relative_path is not None
        full_path = tmp_path / relative_path
        assert full_path.exists()

    async def test_save_sanitizes_filename(self, storage, tmp_path):
        """Deve sanitizar nomes de arquivo perigosos."""
        content = b"test content"
        relative_path = await storage.save(content, "../../../etc/passwd")

        full_path = tmp_path / relative_path
        assert full_path.exists()
        assert "passwd" in full_path.name

    async def test_get_path(self, storage, tmp_path):
        """Deve retornar caminho absoluto para caminho relativo."""
        content = b"test"
        relative = await storage.save(content, "file.txt")

        abs_path = await storage.get_path(relative)

        assert isinstance(abs_path, Path)
        assert abs_path.is_absolute()
        assert abs_path.exists()

    async def test_delete_file(self, storage, tmp_path):
        """Deve deletar arquivo existente."""
        content = b"test"
        relative = await storage.save(content, "file.txt")

        result = await storage.delete(relative)

        assert result is True
        assert not (tmp_path / relative).exists()

    async def test_delete_nonexistent_file(self, storage):
        """Deve retornar False para arquivo inexistente."""
        result = await storage.delete("nonexistent.txt")

        assert result is False

    async def test_exists_true(self, storage):
        """Deve retornar True para arquivo existente."""
        content = b"test"
        relative = await storage.save(content, "file.txt")

        exists = await storage.exists(relative)

        assert exists is True

    async def test_exists_false(self, storage):
        """Deve retornar False para arquivo inexistente."""
        exists = await storage.exists("nonexistent.txt")

        assert exists is False
