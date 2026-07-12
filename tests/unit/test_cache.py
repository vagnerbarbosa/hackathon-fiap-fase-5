"""Testes para implementações de cache."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.infrastructure.cache.cache_interface import CacheInterface
from src.infrastructure.cache.in_memory_cache import InMemoryCache
from src.infrastructure.cache.cache_factory import CacheFactory
from src.domain.models import ArchitectureGraph, DetectedComponent, BoundingBox, Point


class TestInMemoryCache:
    """Testes para InMemoryCache."""

    @pytest.fixture
    def cache(self):
        """Cache em memória para testes."""
        return InMemoryCache()

    @pytest.fixture
    def sample_graph(self):
        """ArchitectureGraph de exemplo."""
        return ArchitectureGraph(
            components=[
                DetectedComponent(
                    id="test-1",
                    type="database",
                    confidence=0.95,
                    bbox=BoundingBox(x_min=0, y_min=0, x_max=100, y_max=100),
                    center=Point(x=50, y=50),
                )
            ],
            data_flows=[],
            trust_boundaries=[["test-1"]],
        )

    @pytest.fixture
    def temp_image(self):
        """Cria arquivo temporário para testes."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            # Escreve header PNG mínimo
            f.write(b'\x89PNG\r\n\x1a\n')
            f.write(b'\x00' * 100)  # Conteúdo dummy
            path = f.name
        yield path
        os.unlink(path)

    @pytest.mark.asyncio
    async def test_get_returns_none_for_missing_key(self, cache, temp_image):
        """Get retorna None para chave inexistente."""
        result = await cache.get(Path(temp_image))
        assert result is None

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache, temp_image, sample_graph):
        """Set e Get funcionam corretamente."""
        await cache.set(Path(temp_image), sample_graph)
        result = await cache.get(Path(temp_image))

        assert result is not None
        assert isinstance(result, ArchitectureGraph)
        assert len(result.components) == 1
        assert result.components[0].type == "database"

    @pytest.mark.asyncio
    async def test_invalidate_removes_item(self, cache, temp_image, sample_graph):
        """Invalidate remove item do cache."""
        await cache.set(Path(temp_image), sample_graph)
        await cache.invalidate(Path(temp_image))

        result = await cache.get(Path(temp_image))
        assert result is None

    @pytest.mark.asyncio
    async def test_clear_removes_all(self, cache, temp_image, sample_graph):
        """Clear remove todos os itens."""
        await cache.set(Path(temp_image), sample_graph)
        await cache.clear()

        result = await cache.get(Path(temp_image))
        assert result is None

    @pytest.mark.asyncio
    async def test_health_check_returns_true(self, cache):
        """Health check sempre retorna True."""
        assert await cache.health_check() is True

    @pytest.mark.asyncio
    async def test_ttl_expiration(self, cache, temp_image, sample_graph):
        """Itens expiram após TTL."""
        # Reduz TTL para teste
        cache.TTL_SECONDS = 0.01

        await cache.set(Path(temp_image), sample_graph)

        # Aguarda expiração
        import asyncio
        await asyncio.sleep(0.02)

        # Deve estar expirado
        result = await cache.get(Path(temp_image))
        assert result is None


class TestCacheFactory:
    """Testes para CacheFactory."""

    def test_create_in_memory_cache(self):
        """Cria cache em memória."""
        cache = CacheFactory.create_in_memory_cache()
        assert isinstance(cache, InMemoryCache)

    def test_create_redis_cache_raises_on_failure(self):
        """Criar Redis cache lança exceção se falhar."""
        with pytest.raises(Exception):
            CacheFactory.create_redis_cache("redis://invalid:9999")

    @patch('src.infrastructure.cache.cache_factory.RedisCache')
    def test_create_cache_fallback_to_memory(self, mock_redis):
        """Create_cache faz fallback para memória."""
        mock_redis.side_effect = Exception("Redis unavailable")

        cache = CacheFactory.create_cache()

        assert isinstance(cache, InMemoryCache)


class TestCacheInterface:
    """Testes para interface CacheInterface."""

    def test_interface_is_abstract(self):
        """Interface não pode ser instanciada."""
        with pytest.raises(TypeError):
            CacheInterface()

    def test_in_memory_implements_interface(self):
        """InMemoryCache implementa a interface."""
        cache = InMemoryCache()
        assert isinstance(cache, CacheInterface)
