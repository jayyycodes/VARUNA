"""
MOSDAC Convective Lightning & Squall Intelligence — owner: Cbum (Atharva Sarnaik)

Estimates convective squall and marine lightning strike risks over Indian coastal waters.
Currently operates on meteorological convective proxies (CAPE, precipitation probability,
relative humidity, and thermal instability) pending full ISRO MOSDAC WMS/WCS endpoint credentials.

MOSDAC WMS Integration Roadmap:
- Satellite: INSAT-3D / INSAT-3DR / INSAT-3DS
- Layers: Lightning Flash Density, Cloud Top Temperature (CTT), Convective Cloud Index
- Base URL: https://mosdac.gov.in/wms/lightning
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger("mosdac_client")


class MOSDACLightningClient:
    """Convective squall and marine lightning strike risk evaluator."""

    def __init__(self, redis_client=None, timeout: float = 5.0):
        self.redis = redis_client
        self.timeout = timeout
        self.wms_base_url = "https://mosdac.gov.in/wms/lightning"

    def estimate_lightning_risk(
        self,
        rain_probability_pct: float,
        temperature_c: float = 28.0,
        humidity_pct: float = 75.0,
        wind_gusts_kmh: float = 20.0,
    ) -> dict[str, Any]:
        """
        Evaluate convective lightning strike probability and squall threat.
        Uses thermal-convective instability proxy until MOSDAC WMS is authenticated.
        """
        # Convective instability index proxy
        is_high_humidity = humidity_pct >= 75.0
        is_warm_sst = temperature_c >= 27.5
        is_gusty = wind_gusts_kmh >= 35.0

        if rain_probability_pct >= 70.0 and (is_high_humidity or is_gusty):
            risk_level = "high"
            description = "High risk: Severe convective squall and frequent cloud-to-water lightning discharges likely."
            alert_recommended = True
        elif rain_probability_pct >= 40.0:
            risk_level = "moderate"
            description = "Moderate risk: Isolated convective thunderstorms possible in coastal waters."
            alert_recommended = False
        else:
            risk_level = "low"
            description = "Low risk: Stable atmospheric boundary layer, minimal lightning activity expected."
            alert_recommended = False

        return {
            "lightning_risk": risk_level,
            "description": description,
            "alert_recommended": alert_recommended,
            "source": "Precipitation & Convective Instability Heuristic (MOSDAC WMS proxy)",
        }
