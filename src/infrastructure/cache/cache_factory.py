"""Factory para criação de implementações de cache.

Segue o padrão Factory para desacoplar a criação do cache
da sua utilização, permitindo injeção de dependências.
"""

import logging
from typing import Optional

from src.infrastructure.cache.cache_interface import CacheInterface
from src.infrastructure.cache.redis_cache import RedisCache
from src.infrastructure.cache.in_memory_cache import InMemoryCache
from src.core.config import settings

logger = logging.getLogger(__name__)


class CacheFactory:
    """Factory para criar instâncias de cache.

    Tenta criar Redis primeiro, fallback para in-memory.
    """

    @staticmethod
    def create_cache(redis_url: Optional[str] = None) -> CacheInterface:
        """Cria e retorna uma implementação de cache.

        Tenta Redis primeiro, se falhar usa in-memory.

        Args:
            redis_url: URL opcional do Redis. Se None, usa settings.REDIS_URL.

        Returns:
            Instância de CacheInterface (Redis ou InMemory).
        """
        url = redis_url or settings.redis_url

        try:
            cache = RedisCache(url)
            logger.info("CacheFactory: Using Redis cache")
            return cache
        except Exception as e:
            logger.warning(f"CacheFactory: Redis unavailable, using in-memory: {e}")
            return InMemoryCache()

    @staticmethod
    def create_redis_cache(redis_url: Optional[str] = None) -> CacheInterface:
        """Cria cache Redis (lança exceção se falhar).

        Args:
            redis_url: URL do Redis.

        Returns:
            Instância de RedisCache.

        Raises:
            ConnectionError: Se não conseguir conectar ao Redis.
        """
        url = redis_url or settings.redis_url
        return RedisCache(url)

    @staticmethod
    def create_in_memory_cache() -> CacheInterface:
        """Cria cache em memória.

        Returns:
            Instância de InMemoryCache.
        """
        return InMemoryCache()
