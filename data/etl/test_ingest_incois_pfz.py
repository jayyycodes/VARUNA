"""
Unit tests for data/etl/ingest_incois_pfz.py and data/etl/scheduler.py
Tests seed feature generation, 7 coastal states coverage, GeoJSON validation, local caching, and 6-hour scheduler.
"""

import json
import os
import tempfile
from datetime import date
from unittest.mock import MagicMock, patch
import pytest

from data.etl.ingest_incois_pfz import (
    TARGET_COASTAL_STATES,
    generate_seed_features,
    ingest_features_into_db,
    run_ingestion,
    initialize_pfz_schema,
    validate_pfz_feature,
    validate_pfz_geojson,
    cache_pfz_geojson,
)
from data.etl.scheduler import scheduled_ingestion_tick


def test_generate_seed_features_all_7_states():
    d = date(2026, 9, 12)
    features = generate_seed_features(d)
    assert len(features) >= 7

    states_found = set()
    for feat in features:
        assert feat["type"] == "Feature"
        assert feat["geometry"]["type"] == "LineString"
        assert len(feat["geometry"]["coordinates"]) >= 2
        props = feat["properties"]
        assert props["advisory_date"] == "2026-09-12"
        assert "sector_name" in props
        assert "state" in props
        assert "depth_m" in props
        assert props["depth_m"] > 0
        states_found.add(props["state"])

    # Ensure all 7 requested coastal states are covered
    expected_states = set(TARGET_COASTAL_STATES)
    assert expected_states.issubset(states_found), f"Missing states: {expected_states - states_found}"


def test_validate_pfz_feature_valid_and_invalid():
    # Valid LineString feature
    valid_feat = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [[73.12, 16.98], [73.05, 17.05]],
        },
        "properties": {
            "advisory_id": "TEST-01",
            "state": "Maharashtra",
            "advisory_date": "2026-09-12",
        },
    }
    is_valid, err = validate_pfz_feature(valid_feat)
    assert is_valid is True
    assert err is None

    # Invalid - non-Feature type
    invalid_type = dict(valid_feat, type="InvalidType")
    is_valid, err = validate_pfz_feature(invalid_type)
    assert is_valid is False
    assert "Invalid type" in err

    # Invalid - coordinates outside Indian EEZ
    invalid_coords = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [[-120.0, 45.0], [-121.0, 46.0]],
        },
        "properties": {"advisory_id": "TEST-02"},
    }
    is_valid, err = validate_pfz_feature(invalid_coords)
    assert is_valid is False
    assert "out of Indian EEZ bounds" in err


def test_validate_pfz_geojson():
    d = date(2026, 9, 12)
    features = generate_seed_features(d)
    
    # Add an invalid feature
    invalid_feat = {"type": "Invalid", "geometry": None}
    mixed_features = features + [invalid_feat]

    valid, invalid = validate_pfz_geojson(mixed_features)
    assert len(valid) == len(features)
    assert len(invalid) == 1
    assert invalid[0]["feature"] == invalid_feat


def test_cache_pfz_geojson():
    with tempfile.TemporaryDirectory() as tmp_dir:
        d = date(2026, 9, 12)
        features = generate_seed_features(d)

        summary = cache_pfz_geojson(features, cache_dir=tmp_dir)
        assert summary["valid_count"] == len(features)
        assert summary["invalid_count"] == 0

        # Check metadata.json existence and content
        meta_path = os.path.join(tmp_dir, "metadata.json")
        assert os.path.exists(meta_path)
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
            assert meta["valid_features_count"] == len(features)
            assert "state_counts" in meta

        # Check state-specific GeoJSON files
        for state in TARGET_COASTAL_STATES:
            slug = state.lower().replace(" ", "_")
            state_file = os.path.join(tmp_dir, f"{slug}_latest.json")
            assert os.path.exists(state_file), f"Missing cache file for {state}"
            with open(state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                assert data["type"] == "FeatureCollection"
                assert data["state"] == state
                assert data["count"] > 0

        # Check combined pfz_all_latest.json
        all_file = os.path.join(tmp_dir, "pfz_all_latest.json")
        assert os.path.exists(all_file)
        with open(all_file, "r", encoding="utf-8") as f:
            all_data = json.load(f)
            assert all_data["type"] == "FeatureCollection"
            assert all_data["count"] == len(features)


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
    with tempfile.TemporaryDirectory() as tmp_dir:
        d = date(2026, 9, 12)
        res = await run_ingestion(d, num_days=2, dry_run=True, force_seed=True, cache_dir=tmp_dir)
        assert res["status"] == "success"
        assert res["dry_run"] is True
        assert res["num_days"] == 2
        assert len(res["dates_processed"]) == 2
        assert res["total_inserted"] > 0
        assert res["cache_summary"] is not None
        assert res["cache_summary"]["valid_count"] > 0


@pytest.mark.asyncio
async def test_scheduled_ingestion_tick():
    with tempfile.TemporaryDirectory() as tmp_dir:
        report = await scheduled_ingestion_tick(dry_run=True, force_seed=True, cache_dir=tmp_dir)
        assert report["status"] == "success"
        assert report["cache_summary"] is not None
