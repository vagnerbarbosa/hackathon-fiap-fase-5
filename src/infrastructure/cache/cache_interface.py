"""Interface abstrata para implementações de cache.

Define contrato para operações de cache, permitindo múltiplas implementações
(Redis, In-Memory, etc.) sem acoplamento rígido.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Any


class CacheInterface(ABC):
    """Interface abstrata para cache de detecção.

    Todas as implementações de cache devem herdar desta classe
    e implementar os métodos abstratos.
    """

    @abstractmethod
    async def get(self, image_path: Path) -> Optional[Any]:
        """Obtém resultado de detecção em cache.

        Args:
            image_path: Caminho para o arquivo de imagem.

        Returns:
            ArchitectureGraph se em cache, None caso contrário.
        """
        pass

    @abstractmethod
    async def set(self, image_path: Path, graph: Any) -> None:
        """Armazena resultado de detecção em cache.

        Args:
            image_path: Caminho para o arquivo de imagem.
            graph: Resultado de detecção a ser armazenado.
        """
        pass

    @abstractmethod
    async def invalidate(self, image_path: Path) -> None:
        """Remove resultado em cache.

        Args:
            image_path: Caminho para o arquivo de imagem.
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Limpa todas as entradas do cache de detecção."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Verifica se o cache está disponível.

        Returns:
            True se o cache está operacional, False caso contrário.
        """
        pass
