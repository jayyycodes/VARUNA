"""
Unit tests for RiskAuditLogger and Rule Versioning.
Tests schema creation SQL, rule versions dictionary, and log persistence.
"""

from unittest.mock import MagicMock
from agents.risk.audit_logger import RiskAuditLogger, RULE_VERSIONS


def test_rule_versions_catalog():
    assert "RULE-GEO-01" in RULE_VERSIONS
    assert "RULE-CYC-01" in RULE_VERSIONS
    assert "RULE-WAVE-01" in RULE_VERSIONS
    assert "RULE-WIND-01" in RULE_VERSIONS
    assert "RULE-LIGHTNING-01" in RULE_VERSIONS
    assert "RULE-COMPOUND-01" in RULE_VERSIONS
    assert "RULE-EVAC-01" in RULE_VERSIONS
    for k, v in RULE_VERSIONS.items():
        assert "v" in v


def test_dry_run_audit_logging():
    logger = RiskAuditLogger()
    success = logger.log_verdict(
        query_run_id="run-audit-dry",
        verdict="SAFE",
        vessel_type="mechanized_trawler",
        reasons=["All parameters within limits"],
        rule_trace={"computed_verdict": "SAFE"},
        latitude=17.0,
        longitude=73.3,
        dry_run=True,
    )
    assert success is True


def test_initialize_schema_with_mock_db():
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    logger = RiskAuditLogger()
    res = logger.initialize_schema(conn=mock_conn)
    assert res is True
    assert mock_cur.execute.called
    executed_sql = mock_cur.execute.call_args[0][0]
    assert "CREATE TABLE IF NOT EXISTS risk_verdicts" in executed_sql
    assert "query_run_id TEXT NOT NULL" in executed_sql
    assert mock_conn.commit.called
