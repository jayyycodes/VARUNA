"""
Unit tests for HistoricalTrendsEngine and Query #7 integration.
"""

import pytest

from agents.marine_fishing.historical_trends import (
    HistoricalTrendReport,
    HistoricalTrendsEngine,
)
from agents.marine_fishing.marine_agent import MarineFishingAgent
from backend.schemas.envelope import AgentEnvelope


def test_historical_trends_konkan_sector():
    report = HistoricalTrendsEngine.get_trend_report(lat=16.99, lon=73.28, sector_hint="Ratnagiri")
    assert isinstance(report, HistoricalTrendReport)
    assert "Ratnagiri" in report.sector or "Konkan" in report.sector
    assert report.overall_status == "DECLINED"
    assert len(report.months) == 12
    assert len(report.sst_baseline_celsius) == 12
    assert len(report.sst_observed_celsius) == 12
    assert len(report.chlorophyll_baseline_mg_m3) == 12
    assert len(report.chlorophyll_observed_mg_m3) == 12
    assert report.mean_sst_anomaly_c > 0.0
    assert report.chlorophyll_deficit_percent > 0.0
    assert "Maharashtra" in report.statutory_reference.act


def test_historical_trends_saurashtra_and_malabar():
    saurashtra = HistoricalTrendsEngine.get_trend_report(lat=20.90, lon=70.36)
    assert "Saurashtra" in saurashtra.sector or "Veraval" in saurashtra.sector
    assert "Gujarat" in saurashtra.statutory_reference.act

    malabar = HistoricalTrendsEngine.get_trend_report(lat=9.93, lon=76.26)
    assert "Malabar" in malabar.sector or "Kochi" in malabar.sector
    assert "Kerala" in malabar.statutory_reference.act


def test_historical_trends_east_coast():
    coromandel = HistoricalTrendsEngine.get_trend_report(lat=13.08, lon=80.27, sector_hint="Chennai")
    assert "Coromandel" in coromandel.sector or "Chennai" in coromandel.sector
    assert "Tamil Nadu" in coromandel.statutory_reference.act

    vizag = HistoricalTrendsEngine.get_trend_report(lat=17.68, lon=83.21)
    assert "Northern Circars" in vizag.sector or "Visakhapatnam" in vizag.sector
    assert "Andhra Pradesh" in vizag.statutory_reference.act


def test_list_available_sectors():
    sectors = HistoricalTrendsEngine.list_available_sectors()
    assert len(sectors) >= 5
    keys = [s["key"] for s in sectors]
    assert "konkan" in keys
    assert "saurashtra" in keys
    assert "malabar" in keys


@pytest.mark.asyncio
async def test_marine_agent_analyze_historical_trends():
    agent = MarineFishingAgent()
    envelope = await agent.analyze_historical_trends(lat=16.99, lon=73.28, sector_name="Ratnagiri")
    assert isinstance(envelope, AgentEnvelope)
    assert envelope.status == "success"
    assert envelope.agent == "marine_fishing"
    assert "productivity_index" in envelope.data
    assert "statutory_reference" in envelope.data
    assert envelope.confidence >= 0.90
