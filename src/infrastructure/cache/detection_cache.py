"""Cache Redis para resultados de detecção.

Armazena resultados ArchitectureGraph indexados por hash da imagem (SHA-256).
TTL: 1 hora (3600 segundos).

DEPRECATED: Use CacheFactory para criar instâncias de cache.
Esta classe mantém compatibilidade, mas agora usa abstração.
"""

import logging
from pathlib import Path
from typing import Optional

from src.infrastructure.cache.cache_interface import CacheInterface
from src.infrastructure.cache.cache_factory import CacheFactory
from src.domain.models import ArchitectureGraph

logger = logging.getLogger(__name__)


class DetectionCache:
    """Cache para resultados de detecção de componentes.

    Wrapper que usa CacheFactory para criar a implementação apropriada.
    Mantém compatibilidade com código existente.

    Uso:
        >>> cache = DetectionCache()
        >>> graph = cache.get("/path/to/image.png")
        >>> if graph is None:
        ...     graph = detect_components(image_path)
        ...     cache.set("/path/to/image.png", graph)

    NOTA: Para novo código, prefira usar CacheFactory diretamente:
        >>> from src.infrastructure.cache import CacheFactory
        >>> cache = CacheFactory.create_cache()
    """

    def __init__(self, redis_url: Optional[str] = None):
        """Inicializa cache usando factory.

        Args:
            redis_url: URL do Redis. Se None, usa settings.REDIS_URL.
        """
        self._cache: CacheInterface = CacheFactory.create_cache(redis_url)
        self._impl_name = type(self._cache).__name__
        logger.info(f"DetectionCache initialized with {self._impl_name}")

    async def get(self, image_path: Path) -> Optional[ArchitectureGraph]:
        """Obtém resultado de detecção em cache.

        Args:
            image_path: Caminho para o arquivo de imagem.

        Returns:
            ArchitectureGraph se em cache, None caso contrário.
        """
        result = await self._cache.get(image_path)
        return result if isinstance(result, ArchitectureGraph) else None

    async def set(self, image_path: Path, graph: ArchitectureGraph) -> None:
        """Armazena resultado de detecção em cache.

        Args:
            image_path: Caminho para o arquivo de imagem.
            graph: Resultado de detecção a ser armazenado.
        """
        await self._cache.set(image_path, graph)

    async def invalidate(self, image_path: Path) -> None:
        """Remove resultado em cache.

        Args:
            image_path: Caminho para o arquivo de imagem.
        """
        await self._cache.invalidate(image_path)

    async def clear(self) -> None:
        """Limpa todas as entradas do cache de detecção."""
        await self._cache.clear()

    async def health_check(self) -> bool:
        """Verifica se o cache está disponível.

        Returns:
            True se o cache está operacional.
        """
        return await self._cache.health_check()
