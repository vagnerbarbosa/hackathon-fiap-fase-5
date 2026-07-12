"""Tests for LocalFileStorage."""

import pytest
from pathlib import Path

from src.infrastructure.storage import LocalFileStorage


class TestLocalFileStorage:
    """Test LocalFileStorage operations."""

    @pytest.fixture
    def storage(self, tmp_path):
        """Create a storage instance with temp directory."""
        return LocalFileStorage(base_path=str(tmp_path))

    async def test_save_file(self, storage, tmp_path):
        """Should save file and return relative path."""
        content = b"test content"
        relative_path = await storage.save(content, "test.txt")

        assert relative_path is not None
        full_path = tmp_path / relative_path
        assert full_path.exists()
        assert full_path.read_bytes() == content

    async def test_save_file_without_filename(self, storage, tmp_path):
        """Should generate filename if not provided."""
        content = b"test content"
        relative_path = await storage.save(content)

        assert relative_path is not None
        full_path = tmp_path / relative_path
        assert full_path.exists()

    async def test_save_sanitizes_filename(self, storage, tmp_path):
        """Should sanitize dangerous filenames."""
        content = b"test content"
        relative_path = await storage.save(content, "../../../etc/passwd")

        full_path = tmp_path / relative_path
        assert full_path.exists()
        assert "passwd" in full_path.name

    async def test_get_path(self, storage, tmp_path):
        """Should return absolute path for relative path."""
        content = b"test"
        relative = await storage.save(content, "file.txt")

        abs_path = await storage.get_path(relative)

        assert isinstance(abs_path, Path)
        assert abs_path.is_absolute()
        assert abs_path.exists()

    async def test_delete_file(self, storage, tmp_path):
        """Should delete existing file."""
        content = b"test"
        relative = await storage.save(content, "file.txt")

        result = await storage.delete(relative)

        assert result is True
        assert not (tmp_path / relative).exists()

    async def test_delete_nonexistent_file(self, storage):
        """Should return False for non-existent file."""
        result = await storage.delete("nonexistent.txt")

        assert result is False

    async def test_exists_true(self, storage):
        """Should return True for existing file."""
        content = b"test"
        relative = await storage.save(content, "file.txt")

        exists = await storage.exists(relative)

        assert exists is True

    async def test_exists_false(self, storage):
        """Should return False for non-existent file."""
        exists = await storage.exists("nonexistent.txt")

        assert exists is False
