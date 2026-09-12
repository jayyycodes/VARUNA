"""
Tests for IMD RSMC Cyclone Bulletin Parsing and Client — owner: Cbum
"""

import pytest
from agents.weather.imd_bulletin import (
    IMDBulletin,
    IMDCycloneClient,
    IMDParser,
    haversine_distance_km,
)

SAMPLE_IMD_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>IMD RSMC Tropical Cyclone Bulletins</title>
    <link>https://rsmcnewdelhi.imd.gov.in</link>
    <description>Tropical Cyclone Advisories for North Indian Ocean</description>
    <item>
      <title>BULLETIN NO. 14: SEVERE CYCLONIC STORM DANA OVER NORTH BAY OF BENGAL</title>
      <description>
        The Severe Cyclonic Storm DANA over North Bay of Bengal moved north-northwestwards.
        Centered at 0300 UTC near latitude 19.5 N and longitude 86.8 E, about 210 km south-southeast of Paradip (Odisha Coast).
        Maximum sustained surface wind speed is 55 knots gusting to 65 knots.
        Port Warning Signal No. 8 hoisted at Paradip and Dhamra ports.
      </description>
      <pubDate>Thu, 24 Oct 2026 06:00:00 +0530</pubDate>
      <guid>IMD-RSMC-DANA-014</guid>
    </item>
  </channel>
</rss>
"""


def test_parse_xml_feed_success():
    bulletin = IMDParser.parse_xml_feed(SAMPLE_IMD_RSS)
    assert bulletin is not None
    assert bulletin.storm_name == "Dana"
    assert bulletin.intensity_category == "Severe Cyclonic Storm"
    assert bulletin.center_lat == 19.5
    assert bulletin.center_lon == 86.8
    assert bulletin.max_sustained_wind_kts == 55.0
    assert bulletin.max_gusts_kts == 65.0
    assert bulletin.port_warning_signal == 8
    assert "Odisha Coast" in bulletin.affected_coastal_regions


def test_parse_empty_or_invalid_xml():
    assert IMDParser.parse_xml_feed("") is None
    assert IMDParser.parse_xml_feed("   ") is None
    
    # Non-XML text with cyclone info falls back to regex parse
    raw = "Cyclonic Storm Fani near 15.0 N, 85.0 E with wind 45 knots. Signal 3."
    bulletin = IMDParser.parse_raw_text(raw)
    assert bulletin is not None
    assert bulletin.storm_name == "Fani"
    assert bulletin.center_lat == 15.0
    assert bulletin.center_lon == 85.0
    assert bulletin.max_sustained_wind_kts == 45.0
    assert bulletin.port_warning_signal == 3


def test_haversine_distance():
    # Distance between Paradip (20.3167, 86.6114) and Puri (19.8135, 85.8312) is ~99 km
    dist = haversine_distance_km(20.3167, 86.6114, 19.8135, 85.8312)
    assert 90.0 <= dist <= 110.0


@pytest.mark.asyncio
async def test_client_cyclone_threat_detection(monkeypatch):
    client = IMDCycloneClient(redis_client=None)

    # Mock get_latest_bulletin to return parsed bulletin
    mock_bulletin = IMDParser.parse_xml_feed(SAMPLE_IMD_RSS)
    async def mock_get():
        return mock_bulletin

    monkeypatch.setattr(client, "get_latest_bulletin", mock_get)

    # Nearby point (20.0, 87.0) is within 100km of storm center (19.5, 86.8)
    threat = await client.check_cyclone_threat(20.0, 87.0, radius_km=300.0)
    assert threat is not None
    assert threat["threat_level"] == "CRITICAL"
    assert threat["storm_name"] == "Dana"
    assert threat["port_signal"] == 8

    # Far away point (Mumbai 18.9, 72.8) is ~1400km away
    threat_far = await client.check_cyclone_threat(18.9, 72.8, radius_km=300.0)
    assert threat_far is None
