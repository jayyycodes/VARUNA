"""
Varuna (ORCA) — Risk Verdict Audit Logger & Threshold Versioning Engine.
Persists deterministic safety verdicts, rule traces, and rule versions into
PostgreSQL/PostGIS (risk_verdicts table) for maritime accident investigation audits.

Owner: Jaish
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import psycopg2
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("varuna.risk_audit")

# Authoritative Rule Versions (Accident Investigation Audit Catalog)
RULE_VERSIONS: Dict[str, str] = {
    "RULE-GEO-01": "v2.0 (Maritime Zones of India Act 1976/1981)",
    "RULE-CYC-01": "v2.0 (IMD RSMC Cyclone Mandatory Zero-Departure)",
    "RULE-WAVE-01": "v2.1 (INCOIS OSF Vessel-Scaled Wave Height)",
    "RULE-WIND-01": "v2.1 (IMD Beaufort Scale 6 Vessel-Scaled Wind)",
    "RULE-LIGHTNING-01": "v1.5 (IMD Convective Storm Severe Lightning)",
    "RULE-COMPOUND-01": "v1.2 (Beam Seas / Cross Swell Angle Interaction)",
    "RULE-COMPOUND-02": "v1.2 (Opposing Current Wave Steepening Interaction)",
    "RULE-COMPOUND-03": "v1.1 (Shallow-Water Shoaling Coastal Breakers)",
    "RULE-EVAC-01": "v1.0 (Time-to-Shelter Squall Intercept Margin)",
}


class RiskAuditLogger:
    """Manages persistence of risk verdicts and audit telemetry into PostgreSQL."""

    def __init__(self) -> None:
        self.host = os.getenv("POSTGRES_HOST", "127.0.0.1")
        self.port = int(os.getenv("POSTGRES_PORT", "5433"))
        self.db = os.getenv("POSTGRES_DB", "varuna")
        self.user = os.getenv("POSTGRES_USER", "varuna")
        self.password = os.getenv("POSTGRES_PASSWORD", "varuna_dev")

    def _get_connection(self):
        return psycopg2.connect(
            dbname=self.db,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
        )

    def initialize_schema(self, conn=None) -> bool:
        """Creates risk_verdicts audit table and indices if they do not exist."""
        close_conn = False
        if conn is None:
            try:
                conn = self._get_connection()
                close_conn = True
            except Exception as exc:
                logger.warning("Could not connect to PostgreSQL for schema init: %s", exc)
                return False

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS risk_verdicts (
                        id SERIAL PRIMARY KEY,
                        query_run_id TEXT NOT NULL,
                        verdict TEXT NOT NULL,
                        vessel_type TEXT NOT NULL,
                        reasons JSONB NOT NULL,
                        rule_trace JSONB NOT NULL,
                        rules_triggered JSONB,
                        rule_versions JSONB,
                        latitude DOUBLE PRECISION,
                        longitude DOUBLE PRECISION,
                        created_at TIMESTAMPTZ DEFAULT now()
                    );
                    CREATE INDEX IF NOT EXISTS idx_risk_verdicts_run_id
                        ON risk_verdicts (query_run_id);
                    CREATE INDEX IF NOT EXISTS idx_risk_verdicts_verdict
                        ON risk_verdicts (verdict);
                    CREATE INDEX IF NOT EXISTS idx_risk_verdicts_vessel
                        ON risk_verdicts (vessel_type);
                """)
                conn.commit()
            return True
        except Exception as exc:
            logger.error("Failed to initialize risk_verdicts schema: %s", exc)
            return False
        finally:
            if close_conn and conn:
                conn.close()

    def log_verdict(
        self,
        query_run_id: str,
        verdict: str,
        vessel_type: str,
        reasons: List[str],
        rule_trace: Dict[str, Any],
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        dry_run: bool = False,
    ) -> bool:
        """
        Persists a single risk verdict audit record with rule versioning.
        Returns True on success, False if database was offline.
        """
        if dry_run:
            logger.info("[DRY-RUN] Audited verdict %s for query %s", verdict, query_run_id)
            return True

        triggered = rule_trace.get("triggered_rules", [])

        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                sql = """
                    INSERT INTO risk_verdicts (
                        query_run_id, verdict, vessel_type, reasons,
                        rule_trace, rules_triggered, rule_versions,
                        latitude, longitude, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, now());
                """
                cur.execute(
                    sql,
                    (
                        query_run_id,
                        verdict,
                        vessel_type,
                        json.dumps(reasons),
                        json.dumps(rule_trace),
                        json.dumps(triggered),
                        json.dumps(RULE_VERSIONS),
                        latitude,
                        longitude,
                    ),
                )
                conn.commit()
            conn.close()
            return True
        except Exception as exc:
            logger.warning("Failed to persist risk verdict to DB (offline/unavailable): %s", exc)
            return False
