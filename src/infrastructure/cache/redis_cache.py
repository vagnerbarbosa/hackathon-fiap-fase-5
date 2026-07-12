"""Implementação Redis do CacheInterface."""

import hashlib
import logging
from pathlib import Path
from typing import Optional, Any

from src.infrastructure.cache.cache_interface import CacheInterface
from src.core.config import settings

logger = logging.getLogger(__name__)


class RedisCache(CacheInterface):
    """Implementação de cache usando Redis."""

    TTL_SECONDS = 3600  # 1 hour

    def __init__(self, redis_url: Optional[str] = None):
        """Inicializa cache Redis.

        Args:
            redis_url: URL do Redis. Se None, usa settings.REDIS_URL.
        """
        self._redis_url = redis_url or settings.redis_url
        self._redis = None
        self._connect()

    def _connect(self) -> None:
        """Conecta ao Redis."""
        try:
            import redis.asyncio as redis

            self._redis = redis.from_url(
                self._redis_url,
                decode_responses=True,
            )
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

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

    async def get(self, image_path: Path) -> Optional[Any]:
        """Obtém do cache."""
        from src.domain.models import ArchitectureGraph

        image_hash = self._compute_hash(image_path)
        key = self._make_key(image_hash)

        try:
            data = await self._redis.get(key)
            if data:
                logger.info(f"Redis cache hit for {image_path.name}")
                return ArchitectureGraph.model_validate_json(data)
        except Exception as e:
            logger.warning(f"Redis get error: {e}")

        return None

    async def set(self, image_path: Path, graph: Any) -> None:
        """Armazena no cache."""
        image_hash = self._compute_hash(image_path)
        key = self._make_key(image_hash)
        data = graph.model_dump_json()

        try:
            await self._redis.setex(key, self.TTL_SECONDS, data)
            logger.info(f"Cached in Redis: {image_path.name}")
        except Exception as e:
            logger.warning(f"Redis set error: {e}")
            raise

    async def invalidate(self, image_path: Path) -> None:
        """Remove do cache."""
        image_hash = self._compute_hash(image_path)
        key = self._make_key(image_hash)

        try:
            await self._redis.delete(key)
            logger.info(f"Invalidated cache for {image_path.name}")
        except Exception as e:
            logger.warning(f"Redis delete error: {e}")

    async def clear(self) -> None:
        """Limpa todas as entradas."""
        try:
            cursor = 0
            while True:
                cursor, keys = await self._redis.scan(
                    cursor=cursor,
                    match="detection:*",
                    count=100,
                )
                if keys:
                    await self._redis.delete(*keys)
                if cursor == 0:
                    break
            logger.info("Cleared Redis cache")
        except Exception as e:
            logger.warning(f"Redis clear error: {e}")

    async def health_check(self) -> bool:
        """Verifica conexão Redis."""
        try:
            await self._redis.ping()
            return True
        except Exception:
            return False
