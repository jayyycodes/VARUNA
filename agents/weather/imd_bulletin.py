"""
IMD RSMC Cyclone Bulletin Ingestion & Parser — owner: Cbum (Atharva Sarnaik)

Fetches and parses real-time Tropical Cyclone Advisories and Bulletins
issued by the India Meteorological Department (IMD) Regional Specialized
Meteorological Centre (RSMC) New Delhi.

WHY xml.etree.ElementTree WAS CHOSEN OVER feedparser / BS4:
-----------------------------------------------------------
1. Zero Dependency Overhead: Standard library `xml.etree.ElementTree` avoids
   introducing external package vulnerabilities or version conflicts in
   production maritime deployments.
2. Resilient Fallback Regex: Government RSS feeds occasionally serve CDATA or
   un-escaped HTML inside XML nodes. A combination of ElementTree for structured
   RSS items and defensive regular expressions guarantees deterministic parsing
   even when RSS formatting deviates from standard XML.
3. High Performance: ElementTree is written in C (FastElementTree) and has negligible
   latency overhead when run in high-throughput async agent loops.
"""

from __future__ import annotations

import asyncio
import logging
import math
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Optional
import xml.etree.ElementTree as ET

import httpx

from backend.gateway.circuit_breaker import circuit_registry

logger = logging.getLogger("imd_bulletin")

IMD_RSMC_RSS_URLS = [
    "https://rsmcnewdelhi.imd.gov.in/rss.xml",
    "https://rsmcnewdelhi.imd.gov.in/images/bulletin/rsmc.xml",
    "https://mausam.imd.gov.in/responsive/cyclone_rss.php",
]

CACHE_KEY_IMD_BULLETIN = "varuna:imd:bulletin:latest"
CACHE_TTL_IMD_BULLETIN = 1800  # 30 minutes


@dataclass
class IMDBulletin:
    bulletin_id: str
    issued_at: str
    storm_name: Optional[str]
    intensity_category: str
    center_lat: Optional[float]
    center_lon: Optional[float]
    max_sustained_wind_kts: Optional[float]
    max_gusts_kts: Optional[float]
    port_warning_signal: Optional[int]
    affected_coastal_regions: list[str]
    raw_text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IMDBulletin:
        return cls(**data)


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points in km."""
    R = 6371.0  # Earth's radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


class IMDParser:
    """Parser for IMD RSMC RSS and bulletin textual content."""

    # Storm category classifications according to IMD Scale
    CATEGORIES = [
        ("Super Cyclonic Storm", 120.0),
        ("Extremely Severe Cyclonic Storm", 90.0),
        ("Very Severe Cyclonic Storm", 64.0),
        ("Severe Cyclonic Storm", 48.0),
        ("Cyclonic Storm", 34.0),
        ("Deep Depression", 28.0),
        ("Depression", 17.0),
    ]

    @classmethod
    def parse_xml_feed(cls, xml_content: str) -> Optional[IMDBulletin]:
        """Parse RSS/XML feed string into an IMDBulletin dataclass."""
        if not xml_content or not xml_content.strip():
            return None

        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as err:
            logger.warning(f"[imd_bulletin] XML parse error: {err}. Attempting regex fallback.")
            return cls.parse_raw_text(xml_content)

        # Look for items in RSS channel
        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else root.findall(".//item")

        if not items:
            # Check if root itself is a direct bulletin node
            return cls.parse_raw_text(xml_content)

        # Process the latest item (first item in RSS)
        latest_item = items[0]
        title = (latest_item.findtext("title") or "").strip()
        description = (latest_item.findtext("description") or "").strip()
        pub_date = (latest_item.findtext("pubDate") or "").strip()
        guid = (latest_item.findtext("guid") or f"imd-{int(datetime.now(timezone.utc).timestamp())}").strip()

        combined_text = f"{title}\n{description}"
        bulletin = cls.parse_raw_text(combined_text, bulletin_id=guid, pub_date=pub_date)
        return bulletin

    @classmethod
    def parse_raw_text(
        cls, text: str, bulletin_id: Optional[str] = None, pub_date: Optional[str] = None
    ) -> Optional[IMDBulletin]:
        """Extract structured cyclone indicators from raw bulletin text using regex."""
        if not text or not text.strip():
            return None

        clean_text = re.sub(r"<[^>]+>", " ", text)  # Strip HTML tags if any

        # 1. Coordinate extraction (e.g. 17.5 N, 84.2 E or latitude 19.5 N and longitude 86.8 E)
        lat: Optional[float] = None
        lon: Optional[float] = None
        
        # Try combined coordinate match first
        coord_match = re.search(
            r"(?:latitude\s*)?(\d{1,2}(?:\.\d+)?)\s*°?\s*N\s*(?:,|and|\/)?\s*(?:longitude\s*)?(\d{2,3}(?:\.\d+)?)\s*°?\s*E",
            clean_text,
            re.IGNORECASE,
        )
        if coord_match:
            try:
                lat = float(coord_match.group(1))
                lon = float(coord_match.group(2))
            except ValueError:
                pass
        else:
            # Try independent lat and lon extraction
            lat_m = re.search(r"(?:latitude|lat\.?)\s*[:=]?\s*(\d{1,2}(?:\.\d+)?)\s*°?\s*N", clean_text, re.IGNORECASE)
            lon_m = re.search(r"(?:longitude|lon\.?|long\.?)\s*[:=]?\s*(\d{2,3}(?:\.\d+)?)\s*°?\s*E", clean_text, re.IGNORECASE)
            if lat_m and lon_m:
                try:
                    lat = float(lat_m.group(1))
                    lon = float(lon_m.group(1))
                except ValueError:
                    pass

        # 2. Wind speed extraction (kts or kmph)
        wind_kts: Optional[float] = None
        wind_match = re.search(
            r"(\d{2,3})\s*(?:knots|kts)", clean_text, re.IGNORECASE
        )
        if wind_match:
            try:
                wind_kts = float(wind_match.group(1))
            except ValueError:
                pass
        else:
            kmph_match = re.search(
                r"(\d{2,3})\s*(?:kmph|km/h|kmph)", clean_text, re.IGNORECASE
            )
            if kmph_match:
                try:
                    wind_kts = round(float(kmph_match.group(1)) / 1.852, 1)
                except ValueError:
                    pass

        # 3. Storm Name
        storm_name: Optional[str] = None
        name_match = re.search(
            r"cyclon(?:e|ic\s+storm)\s+['\"]?([A-Z][a-z]+)['\"]?",
            clean_text,
            re.IGNORECASE,
        )
        if name_match:
            storm_name = name_match.group(1).capitalize()

        # 4. Intensity Classification
        intensity = "Squally Weather / Advisory"
        if wind_kts:
            for cat_name, min_kts in cls.CATEGORIES:
                if wind_kts >= min_kts:
                    intensity = cat_name
                    break
        else:
            for cat_name, _ in cls.CATEGORIES:
                if re.search(rf"\b{re.escape(cat_name)}\b", clean_text, re.IGNORECASE):
                    intensity = cat_name
                    break

        # 5. Port Warning Signal (e.g., Signal No. 8, Signal #3, Distant Cautionary Signal No. I)
        signal: Optional[int] = None
        sig_match = re.search(
            r"(?:signal\s+(?:no\.?|number|#)?\s*|signal\s+)(\d{1,2})",
            clean_text,
            re.IGNORECASE,
        )
        if sig_match:
            try:
                signal = int(sig_match.group(1))
            except ValueError:
                pass

        # 6. Affected Coastal Regions
        regions: list[str] = []
        known_coasts = [
            "North Bay of Bengal",
            "South Bay of Bengal",
            "East Central Bay of Bengal",
            "West Central Bay of Bengal",
            "North Arabian Sea",
            "South Arabian Sea",
            "East Central Arabian Sea",
            "West Central Arabian Sea",
            "Odisha Coast",
            "Andhra Pradesh Coast",
            "Tamil Nadu Coast",
            "West Bengal Coast",
            "Maharashtra Coast",
            "Gujarat Coast",
            "Kerala Coast",
            "Goa Coast",
            "Karnataka Coast",
        ]
        for coast in known_coasts:
            if re.search(rf"\b{re.escape(coast.replace(' Coast', ''))}\b", clean_text, re.IGNORECASE):
                regions.append(coast)

        # Compute gusts (approx 1.35x sustained if not stated)
        gusts_kts: Optional[float] = None
        gust_match = re.search(r"gusting\s+to\s+(\d{2,3})\s*(?:kts|knots|kmph)", clean_text, re.IGNORECASE)
        if gust_match:
            try:
                val = float(gust_match.group(1))
                gusts_kts = val if "kmph" not in gust_match.group(0).lower() else round(val / 1.852, 1)
            except ValueError:
                pass
        if not gusts_kts and wind_kts:
            gusts_kts = round(wind_kts * 1.35, 1)

        b_id = bulletin_id or f"imd-rsmc-{int(datetime.now(timezone.utc).timestamp())}"
        issued = pub_date or datetime.now(timezone.utc).isoformat()

        return IMDBulletin(
            bulletin_id=b_id,
            issued_at=issued,
            storm_name=storm_name,
            intensity_category=intensity,
            center_lat=lat,
            center_lon=lon,
            max_sustained_wind_kts=wind_kts,
            max_gusts_kts=gusts_kts,
            port_warning_signal=signal,
            affected_coastal_regions=regions,
            raw_text=clean_text[:500],
        )


class IMDCycloneClient:
    """Client to fetch and process IMD RSMC cyclone bulletins with circuit breaker & caching."""

    def __init__(self, redis_client=None, timeout: float = 6.0):
        self.redis = redis_client
        self.timeout = timeout

    async def _fetch_from_urls(self) -> Optional[str]:
        """Fetch raw XML/RSS text from IMD endpoints."""
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            for url in IMD_RSMC_RSS_URLS:
                try:
                    res = await client.get(url, headers={"User-Agent": "VARUNA-Maritime-AI/1.0"})
                    if res.status_code == 200 and len(res.text) > 50:
                        return res.text
                except Exception as exc:
                    logger.debug(f"[imd_bulletin] Could not fetch {url}: {exc}")
        return None

    async def get_latest_bulletin(self) -> Optional[IMDBulletin]:
        """Fetch the latest IMD RSMC bulletin, checking cache first."""
        # 1. Check Redis Cache
        if self.redis:
            try:
                import json
                cached = self.redis.get(CACHE_KEY_IMD_BULLETIN)
                if cached:
                    if isinstance(cached, bytes):
                        cached = cached.decode("utf-8")
                    data = json.loads(cached)
                    return IMDBulletin.from_dict(data)
            except Exception as e:
                logger.warning(f"[imd_bulletin] Redis read error: {e}")

        # 2. Fetch with Circuit Breaker
        async def _fetch_wrapper():
            raw = await self._fetch_from_urls()
            if not raw:
                return None
            return IMDParser.parse_xml_feed(raw)

        try:
            bulletin: Optional[IMDBulletin] = await circuit_registry.call(
                "imd_rsmc",
                _fetch_wrapper,
                fallback_factory=lambda: None,
            )
        except Exception as exc:
            logger.warning(f"[imd_bulletin] Circuit breaker call failed: {exc}")
            bulletin = None

        # 3. Cache result if found
        if bulletin and self.redis:
            try:
                import json
                self.redis.setex(
                    CACHE_KEY_IMD_BULLETIN,
                    CACHE_TTL_IMD_BULLETIN,
                    json.dumps(bulletin.to_dict()),
                )
            except Exception as e:
                logger.warning(f"[imd_bulletin] Redis write error: {e}")

        return bulletin

    async def check_cyclone_threat(
        self, lat: float, lon: float, radius_km: float = 400.0
    ) -> Optional[dict[str, Any]]:
        """
        Check if any active IMD bulletin impacts the specified coordinates.
        Returns threat summary dictionary if within danger radius, or None.
        """
        bulletin = await self.get_latest_bulletin()
        if not bulletin:
            return None

        # If bulletin has specific coordinates, calculate distance
        if bulletin.center_lat is not None and bulletin.center_lon is not None:
            dist = haversine_distance_km(lat, lon, bulletin.center_lat, bulletin.center_lon)
            if dist <= radius_km:
                return {
                    "threat_level": "CRITICAL" if bulletin.max_sustained_wind_kts and bulletin.max_sustained_wind_kts >= 48 else "WARNING",
                    "distance_km": round(dist, 1),
                    "storm_name": bulletin.storm_name,
                    "intensity": bulletin.intensity_category,
                    "sustained_wind_kts": bulletin.max_sustained_wind_kts,
                    "port_signal": bulletin.port_warning_signal,
                    "issued_at": bulletin.issued_at,
                    "bulletin_id": bulletin.bulletin_id,
                    "summary": f"IMD Alert: {bulletin.intensity_category} ({bulletin.storm_name or 'Unnamed'}) located {dist:.0f}km away. Sustained wind {bulletin.max_sustained_wind_kts or 'N/A'} kts. Port Warning Signal #{bulletin.port_warning_signal or 'N/A'}.",
                }
        return None
