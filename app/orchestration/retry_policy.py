"""Retry policy for stage execution failures."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

RETRYABLE_ERRORS = (
    "RateLimitError",
    "APIConnectionError",
    "Timeout",
    "ToolExecutionError",
    "NetworkError",
)


class RetryPolicy:
    def __init__(
        self,
        max_retries: int = 3,
        base_delay_seconds: float = 60.0,
        backoff_multiplier: float = 2.0,
        retryable_error_types: tuple = RETRYABLE_ERRORS,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay_seconds
        self.backoff = backoff_multiplier
        self.retryable = retryable_error_types

    def is_retryable(self, error: Exception) -> bool:
        return any(t in type(error).__name__ for t in self.retryable)

    def delay_for(self, attempt: int) -> float:
        return self.base_delay * (self.backoff ** attempt)

    def execute(
        self,
        fn: Callable[[], Any],
        stage_id: str,
        on_retry: Optional[Callable[[int, Exception], None]] = None,
    ) -> Any:
        """
        Execute fn with retry logic.

        Args:
            fn: Callable to execute.
            stage_id: Stage name for logging.
            on_retry: Optional callback(attempt, error) before each retry.
        """
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                return fn()
            except Exception as exc:
                last_error = exc
                if attempt >= self.max_retries or not self.is_retryable(exc):
                    logger.error(
                        "Stage %s failed permanently after %d attempt(s): %s",
                        stage_id,
                        attempt + 1,
                        exc,
                    )
                    raise

                delay = self.delay_for(attempt)
                logger.warning(
                    "Stage %s attempt %d/%d failed (%s). Retrying in %.0fs.",
                    stage_id,
                    attempt + 1,
                    self.max_retries,
                    type(exc).__name__,
                    delay,
                )
                if on_retry:
                    on_retry(attempt + 1, exc)
                time.sleep(delay)

        raise last_error  # type: ignore
