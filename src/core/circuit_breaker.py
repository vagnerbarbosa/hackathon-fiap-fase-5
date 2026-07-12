"""Implementação do padrão Circuit Breaker para resiliência.

Previne cascata de falhas quando serviços externos (IA) estão indisponíveis.
"""

import asyncio
import logging
import time
from enum import Enum
from functools import wraps
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Estados do Circuit Breaker."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit Breaker para proteção contra falhas em cascata.

    Estados:
        - CLOSED: Operação normal, passa requisições
        - OPEN: Serviço falhando, rejeita rapidamente
        - HALF_OPEN: Testando se serviço recuperou

    Exemplo:
        >>> cb = CircuitBreaker(failure_threshold=5, recovery_timeout=30)
        >>> @cb.protect
        ... async def call_ai_service(image):
        ...     return await model.predict(image)
    """

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3,
        expected_exception: type = Exception,
    ):
        """Inicializa Circuit Breaker.

        Args:
            name: Nome identificador do circuito
            failure_threshold: Falhas consecutivas para abrir
            recovery_timeout: Tempo (segundos) antes de tentar recuperação
            half_open_max_calls: Chamadas permitidas em half-open
            expected_exception: Exceção que conta como falha
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.expected_exception = expected_exception

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0

    @property
    def state(self) -> CircuitState:
        """Retorna estado atual do circuito."""
        return self._state

    def _can_execute(self) -> bool:
        """Verifica se execução é permitida."""
        if self._state == CircuitState.CLOSED:
            return True

        if self._state == CircuitState.OPEN:
            # Verifica se passou tempo de recuperação
            if self._last_failure_time:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.recovery_timeout:
                    logger.info(f"Circuit {self.name}: Moving to HALF_OPEN")
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    return True
            logger.warning(f"Circuit {self.name}: OPEN - rejecting request")
            return False

        if self._state == CircuitState.HALF_OPEN:
            if self._half_open_calls < self.half_open_max_calls:
                self._half_open_calls += 1
                return True
            return False

        return True

    def _on_success(self) -> None:
        """Registra sucesso na execução."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.half_open_max_calls:
                logger.info(f"Circuit {self.name}: Closing circuit")
                self._reset()
        else:
            self._failure_count = 0

    def _on_failure(self, exception: Exception) -> None:
        """Registra falha na execução."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            logger.warning(f"Circuit {self.name}: Failure in HALF_OPEN, opening")
            self._state = CircuitState.OPEN
        elif self._failure_count >= self.failure_threshold:
            logger.error(
                f"Circuit {self.name}: Threshold reached ({self._failure_count}), "
                f"opening circuit"
            )
            self._state = CircuitState.OPEN

    def _reset(self) -> None:
        """Reseta estado para CLOSED."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        self._last_failure_time = None

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Executa função protegida pelo circuit breaker.

        Args:
            func: Função a ser executada
            *args: Argumentos posicionais
            **kwargs: Argumentos nomeados

        Returns:
            Resultado da função

        Raises:
            CircuitBreakerOpen: Se circuito está aberto
            Exception: Falha original se função falha
        """
        if not self._can_execute():
            raise CircuitBreakerOpen(
                f"Circuit {self.name} is OPEN - service unavailable"
            )

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure(e)
            raise

    def protect(self, func: Callable) -> Callable:
        """Decorator para proteger função.

        Args:
            func: Função a ser protegida

        Returns:
            Função wrapper protegida
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.call(func, *args, **kwargs)
        return wrapper


class CircuitBreakerOpen(Exception):
    """Exceção lançada quando circuit breaker está aberto."""
    pass
