"""
Resilience & Circuit Breaker Engine for Upstream Services
Protects Varuna / ORCA from cascading failures when upstream marine,
satellite, or LLM providers experience outages or latency spikes.

States:
  - CLOSED: Service is healthy. All calls pass through.
  - OPEN: Service tripped after N consecutive failures. Calls immediately short-circuit.
  - HALF_OPEN: Recovery period elapsed. Allows trial request to probe health.
"""

from __future__ import annotations

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Callable, Coroutine, Optional

logger = logging.getLogger("varuna.circuit_breaker")


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpenError(Exception):
    """Raised when an upstream call is prevented because the circuit is open."""
    def __init__(self, service_name: str, retry_after: float):
        self.service_name = service_name
        self.retry_after = retry_after
        super().__init__(
            f"Circuit breaker for '{service_name}' is OPEN. Retry after {retry_after:.1f}s."
        )


class ServiceBreaker:
    """State tracker for an individual upstream service."""

    def __init__(
        self,
        service_name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
    ):
        self.name = service_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self.state: CircuitState = CircuitState.CLOSED
        self.consecutive_failures: int = 0
        self.total_requests: int = 0
        self.total_failures: int = 0
        self.last_failure_time: float = 0.0
        self.last_success_time: float = 0.0
        self.last_error_message: Optional[str] = None
        self._lock = asyncio.Lock()

    def is_available(self) -> bool:
        """Non-blocking check whether requests should be allowed through."""
        if self.state == CircuitState.CLOSED:
            return True

        now = time.monotonic()
        if self.state == CircuitState.OPEN:
            if (now - self.last_failure_time) >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info(f"[circuit_breaker] Service '{self.name}' transitioned OPEN -> HALF_OPEN (probing)")
                return True
            return False

        # In HALF_OPEN, allow probe
        return True

    def record_success(self):
        """Record successful invocation and close the circuit if half-open."""
        self.consecutive_failures = 0
        self.last_success_time = time.monotonic()
        if self.state != CircuitState.CLOSED:
            logger.info(f"[circuit_breaker] Service '{self.name}' recovered -> CLOSED")
            self.state = CircuitState.CLOSED

    def record_failure(self, error: Exception | str):
        """Record failed invocation and trip circuit if threshold exceeded."""
        self.consecutive_failures += 1
        self.total_failures += 1
        self.last_failure_time = time.monotonic()
        self.last_error_message = str(error)

        if self.consecutive_failures >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                logger.warning(
                    f"[circuit_breaker] Service '{self.name}' TRIPPED after "
                    f"{self.consecutive_failures} failures. State -> OPEN (timeout: {self.recovery_timeout}s)"
                )
            self.state = CircuitState.OPEN

    def to_dict(self) -> dict[str, Any]:
        """Telemetry snapshot for health API endpoints."""
        now = time.monotonic()
        retry_in = max(0.0, self.recovery_timeout - (now - self.last_failure_time)) if self.state == CircuitState.OPEN else 0.0
        uptime_pct = (
            round((1.0 - (self.total_failures / max(1, self.total_requests))) * 100.0, 1)
            if self.total_requests > 0
            else 100.0
        )

        return {
            "service": self.name,
            "state": self.state.value,
            "is_healthy": self.state == CircuitState.CLOSED,
            "consecutive_failures": self.consecutive_failures,
            "failure_threshold": self.failure_threshold,
            "total_requests": self.total_requests,
            "total_failures": self.total_failures,
            "uptime_percent": uptime_pct,
            "retry_in_seconds": round(retry_in, 1) if retry_in > 0 else None,
            "last_error": self.last_error_message,
        }


class CircuitBreakerRegistry:
    """Central registry of all circuit breakers in Varuna."""

    def __init__(self):
        self._breakers: dict[str, ServiceBreaker] = {}
        # Pre-seed standard Varuna external dependencies
        self.register("open_meteo_weather", failure_threshold=3, recovery_timeout=30.0)
        self.register("open_meteo_marine", failure_threshold=3, recovery_timeout=30.0)
        self.register("incois_wfs", failure_threshold=3, recovery_timeout=45.0)
        self.register("noaa_erddap", failure_threshold=3, recovery_timeout=45.0)
        self.register("groq_llm", failure_threshold=3, recovery_timeout=20.0)
        self.register("cerebras_llm", failure_threshold=3, recovery_timeout=20.0)
        self.register("geofencing_postgis", failure_threshold=3, recovery_timeout=15.0)

    def register(
        self,
        service_name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
    ) -> ServiceBreaker:
        if service_name not in self._breakers:
            self._breakers[service_name] = ServiceBreaker(
                service_name, failure_threshold, recovery_timeout
            )
        return self._breakers[service_name]

    def get(self, service_name: str) -> ServiceBreaker:
        if service_name not in self._breakers:
            self.register(service_name)
        return self._breakers[service_name]

    async def call(
        self,
        service_name: str,
        func: Callable[..., Coroutine[Any, Any, Any]],
        *args: Any,
        fallback_factory: Optional[Callable[[], Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Executes an async function guarded by the service's circuit breaker.
        If OPEN and a fallback is provided, immediately invokes fallback without calling func.
        """
        breaker = self.get(service_name)
        breaker.total_requests += 1

        if not breaker.is_available():
            retry_after = max(0.0, breaker.recovery_timeout - (time.monotonic() - breaker.last_failure_time))
            logger.info(f"[circuit_breaker] Fast-failing '{service_name}' (circuit is OPEN).")
            if fallback_factory is not None:
                return fallback_factory()
            raise CircuitBreakerOpenError(service_name, retry_after)

        try:
            res = await func(*args, **kwargs)
            breaker.record_success()
            return res
        except Exception as exc:
            breaker.record_failure(exc)
            if fallback_factory is not None:
                logger.info(f"[circuit_breaker] '{service_name}' failed -> serving fallback.")
                return fallback_factory()
            raise exc

    def get_all_status(self) -> list[dict[str, Any]]:
        return [b.to_dict() for b in self._breakers.values()]


# Global singleton registry
circuit_registry = CircuitBreakerRegistry()
