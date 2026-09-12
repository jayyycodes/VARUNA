"""
Unit tests for data/etl/ingest_incois_pfz.py
Tests seed feature generation, WFS feature ingestion, dry-run mode, and DB schema logic.
"""

from datetime import date
from unittest.mock import MagicMock, patch
import pytest

from data.etl.ingest_incois_pfz import (
    generate_seed_features,
    ingest_features_into_db,
    run_ingestion,
    initialize_pfz_schema,
)


def test_generate_seed_features():
    d = date(2026, 9, 12)
    features = generate_seed_features(d)
    assert len(features) >= 5
    for feat in features:
        assert feat["type"] == "Feature"
        assert feat["geometry"]["type"] == "LineString"
        assert len(feat["geometry"]["coordinates"]) >= 2
        props = feat["properties"]
        assert props["advisory_date"] == "2026-09-12"
        assert "sector_name" in props
        assert "depth_m" in props
        assert props["depth_m"] > 0


def test_ingest_features_dry_run():
    d = date(2026, 9, 12)
    features = generate_seed_features(d)
    inserted, skipped = ingest_features_into_db(None, features, dry_run=True)
    assert inserted == len(features)
    assert skipped == 0


def test_ingest_features_with_mock_db():
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    d = date(2026, 9, 12)
    features = generate_seed_features(d)

    inserted, skipped = ingest_features_into_db(mock_conn, features, dry_run=False)
    assert inserted == len(features)
    assert skipped == 0
    assert mock_cur.execute.call_count == len(features)
    assert mock_conn.commit.called


def test_initialize_pfz_schema():
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    initialize_pfz_schema(mock_conn)
    assert mock_cur.execute.called
    executed_sql = mock_cur.execute.call_args[0][0]
    assert "CREATE TABLE IF NOT EXISTS pfz_advisories" in executed_sql
    assert "USING GIST (geom)" in executed_sql
    assert mock_conn.commit.called


@pytest.mark.asyncio
async def test_run_ingestion_dry_run():
    d = date(2026, 9, 12)
    res = await run_ingestion(d, num_days=2, dry_run=True, force_seed=True)
    assert res["status"] == "success"
    assert res["dry_run"] is True
    assert res["num_days"] == 2
    assert len(res["dates_processed"]) == 2
    assert res["total_inserted"] > 0
