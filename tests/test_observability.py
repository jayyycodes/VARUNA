"""
Tests for LangSmith Observability, Circuit Breakers, and Upstream Health Monitoring.
"""

import time
import pytest
from fastapi.testclient import TestClient

from backend.gateway.circuit_breaker import (
    ServiceBreaker,
    CircuitBreakerRegistry,
    CircuitBreakerOpenError,
    CircuitState,
    circuit_registry,
)
from backend.gateway.observability import log_agent_trajectory, log_llm_span
from backend.main import app


# ═══════════════════════════════════════════════════════════════════════
# 1. Circuit Breaker Unit Tests
# ═══════════════════════════════════════════════════════════════════════

def test_circuit_breaker_closed_to_open_transition():
    """Verify circuit trips to OPEN after threshold failures."""
    breaker = ServiceBreaker(
        service_name="test_service",
        failure_threshold=3,
        recovery_timeout=0.5,
    )
    assert breaker.state == CircuitState.CLOSED
    assert breaker.consecutive_failures == 0
    assert breaker.is_available() is True

    # Failures 1 and 2: still CLOSED
    breaker.record_failure("Err 1")
    assert breaker.state == CircuitState.CLOSED
    assert breaker.consecutive_failures == 1

    breaker.record_failure("Err 2")
    assert breaker.state == CircuitState.CLOSED
    assert breaker.consecutive_failures == 2

    # Failure 3: threshold reached -> trips to OPEN
    breaker.record_failure("Err 3")
    assert breaker.state == CircuitState.OPEN
    assert breaker.is_available() is False


def test_circuit_breaker_half_open_and_recovery():
    """Verify circuit moves from OPEN -> HALF_OPEN -> CLOSED upon successful recovery."""
    breaker = ServiceBreaker(
        service_name="test_recover",
        failure_threshold=2,
        recovery_timeout=0.1,  # short timeout for test
    )

    breaker.record_failure("Err 1")
    breaker.record_failure("Err 2")
    assert breaker.state == CircuitState.OPEN
    assert breaker.is_available() is False

    # Wait for recovery timeout
    time.sleep(0.15)
    # Probing should transition to HALF_OPEN
    assert breaker.is_available() is True
    assert breaker.state == CircuitState.HALF_OPEN

    # Successful call in HALF_OPEN recovers circuit to CLOSED
    breaker.record_success()
    assert breaker.state == CircuitState.CLOSED
    assert breaker.consecutive_failures == 0


@pytest.mark.asyncio
async def test_circuit_registry_call_with_fallback():
    """Verify circuit_registry.call executes fallback when circuit is OPEN or fails."""
    registry = CircuitBreakerRegistry()
    registry.register("flakey_service", failure_threshold=2, recovery_timeout=60.0)

    async def flaky_api():
        raise ConnectionResetError("Connection dropped")

    fallback_data = {"cached_reading": 42}

    # First failure -> fallback invoked
    res1 = await registry.call(
        "flakey_service",
        flaky_api,
        fallback_factory=lambda: fallback_data,
    )
    assert res1 == fallback_data

    # Second failure -> trips circuit to OPEN
    res2 = await registry.call(
        "flakey_service",
        flaky_api,
        fallback_factory=lambda: fallback_data,
    )
    assert res2 == fallback_data
    assert registry.get("flakey_service").state == CircuitState.OPEN

    # Third call: circuit is OPEN -> fast fails directly to fallback without calling flaky_api
    res3 = await registry.call(
        "flakey_service",
        flaky_api,
        fallback_factory=lambda: fallback_data,
    )
    assert res3 == fallback_data


@pytest.mark.asyncio
async def test_circuit_open_error_without_fallback():
    """Verify CircuitBreakerOpenError is raised when OPEN and no fallback factory provided."""
    registry = CircuitBreakerRegistry()
    breaker = registry.register("strict_service", failure_threshold=1, recovery_timeout=60.0)
    breaker.record_failure("Failure")
    assert breaker.state == CircuitState.OPEN

    async def strict_api():
        return "ok"

    with pytest.raises(CircuitBreakerOpenError):
        await registry.call("strict_service", strict_api)


# ═══════════════════════════════════════════════════════════════════════
# 2. Upstream Health API Tests
# ═══════════════════════════════════════════════════════════════════════

def test_health_endpoints_include_upstream_circuits():
    """Verify /health and /api/health/upstream expose circuit breaker statuses."""
    client = TestClient(app)

    # Base /health endpoint
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "upstream_circuits" in data
    assert isinstance(data["upstream_circuits"], list)

    # Dedicated /api/health/upstream endpoint
    res_upstream = client.get("/api/health/upstream")
    assert res_upstream.status_code == 200
    upstream_data = res_upstream.json()
    assert "circuits" in upstream_data
    assert "all_healthy" in upstream_data
    assert isinstance(upstream_data["all_healthy"], bool)


# ═══════════════════════════════════════════════════════════════════════
# 3. LangSmith Observability Unit Tests (Safe Fallback)
# ═══════════════════════════════════════════════════════════════════════

def test_observability_safe_execution_without_crashing():
    """Verify log_agent_trajectory and log_llm_span are resilient and do not crash."""
    # Safe even if LangSmith env vars are missing or network is unavailable
    log_agent_trajectory(
        run_id="test-run-12345",
        agent_name="test_agent",
        intent="weather_safety",
        status="complete",
        latency_ms=45.2,
        inputs={"location": "Ratnagiri"},
        outputs={"status": "complete"},
    )

    log_llm_span(
        role="advisory_generator",
        provider="groq",
        model_name="openai/gpt-oss-120b",
        prompt_messages=[{"role": "user", "content": "Hello"}],
        response_content="Hello Mariner",
        latency_ms=120.5,
    )
