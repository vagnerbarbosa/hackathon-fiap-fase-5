"""Módulos de infraestrutura de cache."""

from src.infrastructure.cache.cache_factory import CacheFactory
from src.infrastructure.cache.cache_interface import CacheInterface
from src.infrastructure.cache.detection_cache import DetectionCache
from src.infrastructure.cache.in_memory_cache import InMemoryCache
from src.infrastructure.cache.redis_cache import RedisCache

__all__ = [
    "CacheInterface",
    "RedisCache",
    "InMemoryCache",
    "CacheFactory",
    "DetectionCache",
]
