"""Implementação em memória do CacheInterface."""

import hashlib
import logging
import time
from pathlib import Path
from typing import Optional, Any, Dict, Tuple

from src.infrastructure.cache.cache_interface import CacheInterface

logger = logging.getLogger(__name__)


class InMemoryCache(CacheInterface):
    """Implementação de cache em memória com TTL.

    Útil para desenvolvimento e testes quando Redis
    não está disponível.
    """

    TTL_SECONDS = 3600  # 1 hour

    def __init__(self):
        """Inicializa cache em memória."""
        self._cache: Dict[str, Tuple[str, float]] = {}  # key: (data, expiry_time)
        logger.info("Initialized in-memory cache")

    def _compute_hash(self, image_path: Path) -> str:
        """Calcula hash SHA-256 do arquivo."""
        sha256 = hashlib.sha256()
        with open(image_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _make_key(self, image_hash: str) -> str:
        """Cria chave de cache."""
        return f"detection:{image_hash}"

    def _cleanup_expired(self) -> None:
        """Remove entradas expiradas do cache."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry) in self._cache.items()
            if expiry < current_time
        ]
        for key in expired_keys:
            del self._cache[key]

    async def get(self, image_path: Path) -> Optional[Any]:
        """Obtém do cache."""
        from src.domain.models import ArchitectureGraph

        self._cleanup_expired()

        image_hash = self._compute_hash(image_path)
        key = self._make_key(image_hash)

        if key in self._cache:
            data, expiry = self._cache[key]
            if time.time() < expiry:
                logger.info(f"Memory cache hit for {image_path.name}")
                return ArchitectureGraph.model_validate_json(data)
            else:
                # Expired
                del self._cache[key]

        return None

    async def set(self, image_path: Path, graph: Any) -> None:
        """Armazena no cache."""
        image_hash = self._compute_hash(image_path)
        key = self._make_key(image_hash)
        data = graph.model_dump_json()
        expiry = time.time() + self.TTL_SECONDS

        self._cache[key] = (data, expiry)
        logger.info(f"Cached in memory: {image_path.name}")

    async def invalidate(self, image_path: Path) -> None:
        """Remove do cache."""
        image_hash = self._compute_hash(image_path)
        key = self._make_key(image_hash)

        if key in self._cache:
            del self._cache[key]
            logger.info(f"Invalidated memory cache for {image_path.name}")

    async def clear(self) -> None:
        """Limpa todas as entradas."""
        self._cache.clear()
        logger.info("Cleared in-memory cache")

    async def health_check(self) -> bool:
        """Sempre disponível."""
        return True
