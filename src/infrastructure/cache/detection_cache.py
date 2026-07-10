"""Redis cache for detection results.

Caches ArchitectureGraph results keyed by image hash (SHA-256).
TTL: 1 hour (3600 seconds).
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional

from src.core.config import settings
from src.domain.models import ArchitectureGraph

logger = logging.getLogger(__name__)


class DetectionCache:
    """Cache for component detection results.

    Uses Redis to cache ArchitectureGraph results by image hash.
    Falls back to in-memory dict if Redis unavailable.

    Usage:
        >>> cache = DetectionCache()
        >>> graph = cache.get("/path/to/image.png")
        >>> if graph is None:
        ...     graph = detect_components(image_path)
        ...     cache.set("/path/to/image.png", graph)
    """

    TTL_SECONDS = 3600  # 1 hour

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize cache with Redis connection.

        Args:
            redis_url: Redis URL. If None, uses settings.REDIS_URL.
        """
        self._redis_url = redis_url or settings.redis_url
        self._redis = None
        self._memory_cache: dict = {}
        self._connect()

    def _connect(self) -> None:
        """Connect to Redis or fallback to memory."""
        try:
            import redis.asyncio as redis

            self._redis = redis.from_url(
                self._redis_url,
                decode_responses=True,
            )
            logger.info("Connected to Redis for detection cache")
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory cache: {e}")
            self._redis = None

    def _compute_hash(self, image_path: Path) -> str:
        """Compute SHA-256 hash of image file.

        Args:
            image_path: Path to image file.

        Returns:
            SHA-256 hex digest of file content.
        """
        sha256 = hashlib.sha256()
        with open(image_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _make_key(self, image_hash: str) -> str:
        """Create cache key from image hash.

        Args:
            image_hash: SHA-256 hash of image.

        Returns:
            Cache key string.
        """
        return f"detection:{image_hash}"

    async def get(self, image_path: Path) -> Optional[ArchitectureGraph]:
        """Get cached detection result.

        Args:
            image_path: Path to image file.

        Returns:
            ArchitectureGraph if cached, None otherwise.
        """
        image_hash = self._compute_hash(image_path)
        key = self._make_key(image_hash)

        try:
            if self._redis:
                data = await self._redis.get(key)
                if data:
                    logger.info(f"Cache hit for {image_path.name}")
                    return ArchitectureGraph.model_validate_json(data)
            else:
                # In-memory fallback
                data = self._memory_cache.get(key)
                if data:
                    logger.info(f"Memory cache hit for {image_path.name}")
                    return ArchitectureGraph.model_validate_json(data)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")

        logger.debug(f"Cache miss for {image_path.name}")
        return None

    async def set(self, image_path: Path, graph: ArchitectureGraph) -> None:
        """Cache detection result.

        Args:
            image_path: Path to image file.
            graph: Detection result to cache.
        """
        image_hash = self._compute_hash(image_path)
        key = self._make_key(image_hash)
        data = graph.model_dump_json()

        try:
            if self._redis:
                await self._redis.setex(key, self.TTL_SECONDS, data)
                logger.info(f"Cached detection result for {image_path.name}")
            else:
                # In-memory fallback (no TTL, manual cleanup needed)
                self._memory_cache[key] = data
                logger.info(f"Cached in memory for {image_path.name}")
        except Exception as e:
            logger.warning(f"Cache set error: {e}")

    async def invalidate(self, image_path: Path) -> None:
        """Remove cached result.

        Args:
            image_path: Path to image file.
        """
        image_hash = self._compute_hash(image_path)
        key = self._make_key(image_hash)

        try:
            if self._redis:
                await self._redis.delete(key)
            else:
                self._memory_cache.pop(key, None)
        except Exception as e:
            logger.warning(f"Cache invalidate error: {e}")

    async def clear(self) -> None:
        """Clear all detection cache entries."""
        try:
            if self._redis:
                # Delete all keys matching "detection:*"
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
            else:
                self._memory_cache.clear()
            logger.info("Cleared detection cache")
        except Exception as e:
            logger.warning(f"Cache clear error: {e}")
