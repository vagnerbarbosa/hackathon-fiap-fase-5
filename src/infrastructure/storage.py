"""File storage service for uploads."""

import os
import shutil
from pathlib import Path
from typing import Optional
from uuid import uuid4

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class LocalFileStorage:
    """Local filesystem storage implementation."""

    def __init__(self, base_path: Optional[str] = None):
        """Initialize storage with base path.

        Args:
            base_path: Base directory for storage. Defaults to settings.storage_path.
        """
        self.base_path = Path(base_path or settings.storage_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save(self, content: bytes, filename: Optional[str] = None) -> str:
        """Save file to storage.

        Args:
            content: File content as bytes.
            filename: Original filename. If None, generates UUID.

        Returns:
            str: Path to saved file (relative to base_path).
        """
        # Generate unique filename
        if filename:
            # Sanitize filename
            safe_name = Path(filename).name.replace("..", "").replace("/", "").replace("\\", "")
            unique_name = f"{uuid4()}_{safe_name}"
        else:
            unique_name = str(uuid4())

        file_path = self.base_path / unique_name

        # Save file
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"File saved: {file_path}", extra_fields={"file_path": str(file_path)})
        return str(file_path.relative_to(self.base_path))

    async def get_path(self, relative_path: str) -> Path:
        """Get absolute path for relative file path.

        Args:
            relative_path: Relative path from base_path.

        Returns:
            Path: Absolute file path.
        """
        return self.base_path / relative_path

    async def delete(self, relative_path: str) -> bool:
        """Delete file from storage.

        Args:
            relative_path: Relative path from base_path.

        Returns:
            bool: True if deleted, False if not found.
        """
        file_path = self.base_path / relative_path

        if not file_path.exists():
            return False

        try:
            if file_path.is_file():
                file_path.unlink()
            else:
                shutil.rmtree(file_path)
            logger.info(f"File deleted: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False

    async def exists(self, relative_path: str) -> bool:
        """Check if file exists.

        Args:
            relative_path: Relative path from base_path.

        Returns:
            bool: True if exists.
        """
        file_path = self.base_path / relative_path
        return file_path.exists()
