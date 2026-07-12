"""Testes para o Circuit Breaker."""

import pytest
import asyncio
from src.core.circuit_breaker import CircuitBreaker, CircuitBreakerOpen


class TestCircuitBreaker:
    """Testes para Circuit Breaker."""

    @pytest.fixture
    def circuit_breaker(self):
        """Circuit breaker para testes."""
        return CircuitBreaker(
            name="test",
            failure_threshold=3,
            recovery_timeout=0.1,  # Curto para testes rápidos
            half_open_max_calls=2,
        )

    @pytest.mark.asyncio
    async def test_initial_state_is_closed(self, circuit_breaker):
        """Estado inicial deve ser CLOSED."""
        assert circuit_breaker.state.value == "closed"

    @pytest.mark.asyncio
    async def test_successful_call_increments_success(self, circuit_breaker):
        """Chamada bem-sucedida mantém estado CLOSED."""
        async def success_func():
            return "success"

        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state.value == "closed"

    @pytest.mark.asyncio
    async def test_failures_open_circuit(self, circuit_breaker):
        """Falhas consecutivas abrem o circuito."""
        async def fail_func():
            raise RuntimeError("error")

        # 3 falhas para abrir
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await circuit_breaker.call(fail_func)

        assert circuit_breaker.state.value == "open"

    @pytest.mark.asyncio
    async def test_open_circuit_rejects_calls(self, circuit_breaker):
        """Circuito aberto rejeita chamadas."""
        async def fail_func():
            raise RuntimeError("error")

        # Abre o circuito
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await circuit_breaker.call(fail_func)

        # Tenta chamar novamente
        async def any_func():
            return "result"

        with pytest.raises(CircuitBreakerOpen):
            await circuit_breaker.call(any_func)

    @pytest.mark.asyncio
    async def test_recovery_to_half_open(self, circuit_breaker):
        """Após timeout, circuito vai para HALF_OPEN."""
        async def fail_func():
            raise RuntimeError("error")

        # Abre o circuito
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await circuit_breaker.call(fail_func)

        assert circuit_breaker.state.value == "open"

        # Espera timeout de recuperação
        await asyncio.sleep(0.15)

        # Próxima chamada deve ir para half-open
        async def success_func():
            return "success"

        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state.value == "half_open"

    @pytest.mark.asyncio
    async def test_success_in_half_open_closes_circuit(self, circuit_breaker):
        """Sucessos em HALF_OPEN fecham o circuito."""
        async def fail_func():
            raise RuntimeError("error")

        async def success_func():
            return "success"

        # Abre o circuito
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await circuit_breaker.call(fail_func)

        # Espera recuperação
        await asyncio.sleep(0.15)

        # Sucessos suficientes para fechar
        for _ in range(2):
            result = await circuit_breaker.call(success_func)
            assert result == "success"

        assert circuit_breaker.state.value == "closed"

    @pytest.mark.asyncio
    async def test_failure_in_half_open_reopens_circuit(self, circuit_breaker):
        """Falha em HALF_OPEN reabre o circuito."""
        async def fail_func():
            raise RuntimeError("error")

        # Abre o circuito
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await circuit_breaker.call(fail_func)

        # Espera recuperação
        await asyncio.sleep(0.15)

        # Falha em half_open reabre
        with pytest.raises(RuntimeError):
            await circuit_breaker.call(fail_func)

        assert circuit_breaker.state.value == "open"

    @pytest.mark.asyncio
    async def test_protect_decorator(self, circuit_breaker):
        """Testa decorator protect."""
        @circuit_breaker.protect
        async def protected_func():
            return "protected"

        result = await protected_func()
        assert result == "protected"

    @pytest.mark.asyncio
    async def test_different_exception_types(self):
        """Circuit breaker filtra tipos de exceção."""
        cb = CircuitBreaker(
            name="test",
            failure_threshold=2,
            expected_exception=ValueError,
        )

        async def value_error():
            raise ValueError("value error")

        async def runtime_error():
            raise RuntimeError("runtime error")

        # ValueError deve contar
        with pytest.raises(ValueError):
            await cb.call(value_error)

        # RuntimeError não deve contar (não é expected)
        with pytest.raises(RuntimeError):
            await cb.call(runtime_error)

        # Circuito ainda fechado
        assert cb.state.value == "closed"

        # Segunda ValueError abre
        with pytest.raises(ValueError):
            await cb.call(value_error)

        assert cb.state.value == "open"
