"""
Unit tests for BathymetryEngine and artisanal gear depth filtering.
"""

import pytest

from agents.marine_fishing.bathymetry import BathymetryEngine


def test_depth_estimation_nearshore_and_offshore():
    # West Coast nearshore (10 km off Ratnagiri)
    nearshore_depth = BathymetryEngine.estimate_depth_meters(16.99, 73.28, distance_from_shore_km=10.0)
    assert 10.0 <= nearshore_depth <= 25.0

    # West Coast shelf-break (80 km offshore)
    offshore_depth = BathymetryEngine.estimate_depth_meters(16.99, 73.28, distance_from_shore_km=80.0)
    assert offshore_depth > 120.0


def test_depth_categories():
    assert BathymetryEngine.categorize_depth(15.0) == "Shallow Coastal (<30m)"
    assert BathymetryEngine.categorize_depth(42.0) == "Inner Continental Shelf (30-50m)"
    assert BathymetryEngine.categorize_depth(110.0) == "Mid-to-Outer Shelf (50-150m)"
    assert BathymetryEngine.categorize_depth(250.0) == "Shelf-Break / Upper Slope (150-300m)"
    assert BathymetryEngine.categorize_depth(800.0) == "Deep Oceanic (>300m)"


def test_artisanal_gear_filtering():
    zones = [
        {"zone_id": "Z1", "lat": 17.05, "lon": 73.25, "distance_km": 12.0, "name": "Nearshore Shoal"},
        {"zone_id": "Z2", "lat": 17.15, "lon": 72.85, "distance_km": 65.0, "name": "Deep Shelf Break"},
    ]

    # Artisanal craft capped at 50m
    artisanal_annotated = BathymetryEngine.filter_and_annotate_zones(zones, vessel_type="artisanal")
    assert len(artisanal_annotated) == 2
    assert artisanal_annotated[0]["gear_compatible"] is True
    assert artisanal_annotated[1]["gear_compatible"] is False
    assert "gear_warning" in artisanal_annotated[1]
    assert "exceeds" in artisanal_annotated[1]["gear_warning"].lower()

    # Deep-sea longliner uncapped
    deep_annotated = BathymetryEngine.filter_and_annotate_zones(zones, vessel_type="deep_sea_longliner")
    assert deep_annotated[0]["gear_compatible"] is True
    assert deep_annotated[1]["gear_compatible"] is True
