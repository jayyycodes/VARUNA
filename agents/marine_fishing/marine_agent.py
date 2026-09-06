"""
Marine & Fishing Intelligence Agent — owner: Jaish

Fetches PFZ advisories, SST, chlorophyll concentration; ranks fishing
zones by productivity, from INCOIS PFZ WebGIS + MOSDAC SST/OCM-3.

See agents/marine_fishing/README.md for full task breakdown (MVP + further stage).
"""

from backend.schemas.envelope import AgentEnvelope


class MarineFishingAgent:
    async def get_ocean_state(self, lat: float, lon: float, date: str) -> AgentEnvelope:
        raise NotImplementedError("TODO: fetch SST + chlorophyll, rank PFZ zones")
