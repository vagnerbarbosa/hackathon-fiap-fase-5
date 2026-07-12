"""Utilitários para retentativas com backoff exponencial.

Implementa estratégias de retry para operações que podem falhar
por razões transientes.
"""

import asyncio
import logging
import random
from functools import wraps
from typing import Callable, Any, Optional, Tuple, Type

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuração para estratégia de retry.

    Attributes:
        max_attempts: Número máximo de tentativas
        base_delay: Delay inicial em segundos
        max_delay: Delay máximo em segundos
        exponential_base: Base para cálculo exponencial
        jitter: Se True, adiciona variação aleatória
        exceptions: Tupla de exceções que disparam retry
    """

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.exceptions = exceptions

    def calculate_delay(self, attempt: int) -> float:
        """Calcula delay para tentativa específica.

        Args:
            attempt: Número da tentativa (1-based)

        Returns:
            Delay em segundos
        """
        delay = self.base_delay * (self.exponential_base ** (attempt - 1))
        delay = min(delay, self.max_delay)

        if self.jitter:
            # Add ±25% jitter
            delay = delay * (0.75 + random.random() * 0.5)

        return delay


async def retry(
    func: Callable,
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> Any:
    """Executa função com retentativas.

    Args:
        func: Função a ser executada
        *args: Argumentos posicionais
        config: Configuração de retry (usa padrão se None)
        **kwargs: Argumentos nomeados

    Returns:
        Resultado da função

    Raises:
        Exception: Última exceção após esgotar tentativas
    """
    cfg = config or RetryConfig()
    last_exception = None

    for attempt in range(1, cfg.max_attempts + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            if attempt > 1:
                logger.info(f"Function succeeded on attempt {attempt}")
            return result

        except cfg.exceptions as e:
            last_exception = e

            if attempt == cfg.max_attempts:
                logger.error(
                    f"Function failed after {cfg.max_attempts} attempts: {e}"
                )
                raise

            delay = cfg.calculate_delay(attempt)
            logger.warning(
                f"Attempt {attempt}/{cfg.max_attempts} failed: {e}. "
                f"Retrying in {delay:.2f}s..."
            )
            await asyncio.sleep(delay)

    raise last_exception


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """Decorator para adicionar retry a função.

    Args:
        max_attempts: Número máximo de tentativas
        base_delay: Delay inicial
        max_delay: Delay máximo
        exceptions: Exceções que disparam retry

    Returns:
        Decorator function
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        exceptions=exceptions,
    )

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry(func, *args, config=config, **kwargs)
        return wrapper
    return decorator


# Configurações pré-definidas para casos comuns

RETRY_FAST = RetryConfig(
    max_attempts=3,
    base_delay=0.5,
    max_delay=5.0,
    exceptions=(ConnectionError, TimeoutError),
)

RETRY_SLOW = RetryConfig(
    max_attempts=5,
    base_delay=2.0,
    max_delay=60.0,
    exceptions=(Exception,),
)

RETRY_AI_SERVICE = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
    exceptions=(ConnectionError, TimeoutError, RuntimeError),
)
