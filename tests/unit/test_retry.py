"""Testes para retry com backoff exponencial."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from src.core.retry import retry, RetryConfig, with_retry, RETRY_FAST, RETRY_SLOW


class TestRetryConfig:
    """Testes para RetryConfig."""

    def test_calculate_delay_no_jitter(self):
        """Cálculo de delay sem jitter."""
        config = RetryConfig(
            base_delay=1.0,
            exponential_base=2.0,
            jitter=False,
        )

        assert config.calculate_delay(1) == 1.0  # 1 * 2^0
        assert config.calculate_delay(2) == 2.0  # 1 * 2^1
        assert config.calculate_delay(3) == 4.0  # 1 * 2^2

    def test_calculate_delay_max_delay(self):
        """Delay respeita limite máximo."""
        config = RetryConfig(
            base_delay=1.0,
            max_delay=5.0,
            exponential_base=2.0,
            jitter=False,
        )

        # Tentativa 4 daria 8.0, mas é limitado a 5.0
        assert config.calculate_delay(4) == 5.0

    def test_calculate_delay_with_jitter(self):
        """Delay com jitter varia entre 75% e 125%."""
        config = RetryConfig(
            base_delay=1.0,
            jitter=True,
        )

        delay = config.calculate_delay(1)
        # 1.0 * 0.75 = 0.75 até 1.0 * 1.25 = 1.25
        assert 0.75 <= delay <= 1.25


class TestRetry:
    """Testes para função retry."""

    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self):
        """Sucesso na primeira tentativa não retry."""
        mock_func = AsyncMock(return_value="success")

        result = await retry(mock_func, config=RETRY_FAST)

        assert result == "success"
        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Retry em caso de falha."""
        mock_func = AsyncMock(
            side_effect=[Exception("fail"), Exception("fail"), "success"]
        )

        config = RetryConfig(
            max_attempts=3,
            base_delay=0.01,  # Rápido para testes
            jitter=False,
            exceptions=(Exception,),
        )

        result = await retry(mock_func, config=config)

        assert result == "success"
        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_raises_after_max_attempts(self):
        """Lança exceção após max tentativas."""
        mock_func = AsyncMock(side_effect=ValueError("error"))

        config = RetryConfig(
            max_attempts=3,
            base_delay=0.01,
            jitter=False,
            exceptions=(ValueError,),
        )

        with pytest.raises(ValueError, match="error"):
            await retry(mock_func, config=config)

        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_different_exception_not_retried(self):
        """Exceções fora da lista não disparam retry."""
        mock_func = AsyncMock(side_effect=RuntimeError("runtime"))

        config = RetryConfig(
            max_attempts=3,
            base_delay=0.01,
            exceptions=(ValueError,),  # Só retry em ValueError
        )

        with pytest.raises(RuntimeError):
            await retry(mock_func, config=config)

        # Não deve ter retry
        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_with_sync_function(self):
        """Retry funciona com funções síncronas."""
        call_count = 0

        def sync_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "success"

        config = RetryConfig(
            max_attempts=3,
            base_delay=0.01,
            jitter=False,
            exceptions=(ValueError,),
        )

        result = await retry(sync_func, config=config)

        assert result == "success"
        assert call_count == 3


class TestWithRetryDecorator:
    """Testes para decorator with_retry."""

    @pytest.mark.asyncio
    async def test_decorator_success(self):
        """Decorator permite sucesso."""
        call_count = 0

        @with_retry(max_attempts=3, base_delay=0.01, exceptions=(ValueError,))
        async def my_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("fail")
            return "success"

        result = await my_func()

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_decorator_failure(self):
        """Decorator propaga falha após tentativas."""
        @with_retry(max_attempts=2, base_delay=0.01, exceptions=(ValueError,))
        async def failing_func():
            raise ValueError("always fails")

        with pytest.raises(ValueError):
            await failing_func()


class TestPredefinedConfigs:
    """Testes para configurações pré-definidas."""

    def test_retry_fast_config(self):
        """RETRY_FAST tem valores adequados."""
        assert RETRY_FAST.max_attempts == 3
        assert RETRY_FAST.base_delay == 0.5
        assert RETRY_FAST.max_delay == 5.0

    def test_retry_slow_config(self):
        """RETRY_SLOW tem valores adequados."""
        assert RETRY_SLOW.max_attempts == 5
        assert RETRY_SLOW.base_delay == 2.0
        assert RETRY_SLOW.max_delay == 60.0
