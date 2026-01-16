# backend/tests/test_geo.py
import pytest
import math
from app.services.geo import haversine_distance_m


class TestHaversineDistance:
    """Test haversine distance calculations."""

    def test_same_point(self):
        """Distance from a point to itself should be 0."""
        point = (40.7128, -74.0060)
        distance = haversine_distance_m(point, point)
        assert distance == pytest.approx(0.0, abs=0.1)

    def test_short_distance(self):
        """Test short distance (about 1km)."""
        # Two points in NYC approximately 1km apart
        point1 = (40.7128, -74.0060)  # Lower Manhattan
        point2 = (40.7228, -74.0060)  # ~1km north
        distance = haversine_distance_m(point1, point2)
        # Should be approximately 1113 meters (1 degree latitude ≈ 111km)
        assert distance == pytest.approx(1113.0, abs=50.0)

    def test_medium_distance(self):
        """Test medium distance (NYC to Philadelphia ~150km)."""
        nyc = (40.7128, -74.0060)
        philly = (39.9526, -75.1652)
        distance = haversine_distance_m(nyc, philly)
        # Should be approximately 150km
        assert distance == pytest.approx(150000, abs=5000)

    def test_long_distance(self):
        """Test long distance (NYC to London ~5500km)."""
        nyc = (40.7128, -74.0060)
        london = (51.5074, -0.1278)
        distance = haversine_distance_m(nyc, london)
        # Should be approximately 5500km
        assert distance == pytest.approx(5500000, abs=100000)

    def test_antipodes(self):
        """Test antipodal points (opposite sides of the globe)."""
        # NYC (40.7128, -74.0060) and its antipode (approximately -40.7128, 105.994)
        point1 = (40.7128, -74.0060)
        point2 = (-40.7128, 105.994)
        distance = haversine_distance_m(point1, point2)
        # Should be approximately half the Earth's circumference
        # Earth's circumference ≈ 40,075 km
        expected = math.pi * 6371000  # Half circumference in meters
        assert distance == pytest.approx(expected, abs=10000)

    def test_equator_crossing(self):
        """Test distance across the equator."""
        point1 = (1.0, 0.0)  # Just north of equator
        point2 = (-1.0, 0.0)  # Just south of equator
        distance = haversine_distance_m(point1, point2)
        # Should be approximately 222km (2 degrees × 111km/degree)
        assert distance == pytest.approx(222000, abs=5000)

    def test_pole_to_equator(self):
        """Test distance from pole to equator."""
        north_pole = (90.0, 0.0)
        equator = (0.0, 0.0)
        distance = haversine_distance_m(north_pole, equator)
        # Should be approximately quarter of Earth's circumference
        expected = (math.pi / 2) * 6371000
        assert distance == pytest.approx(expected, abs=10000)

    def test_same_longitude_different_latitudes(self):
        """Test distance along same longitude."""
        point1 = (40.0, -74.0)
        point2 = (41.0, -74.0)  # 1 degree north
        distance = haversine_distance_m(point1, point2)
        # 1 degree latitude ≈ 111km
        assert distance == pytest.approx(111000, abs=1000)

    def test_same_latitude_different_longitudes(self):
        """Test distance along same latitude."""
        point1 = (40.0, -74.0)
        point2 = (40.0, -73.0)  # 1 degree east
        distance = haversine_distance_m(point1, point2)
        # At 40° latitude, 1 degree longitude ≈ 85km
        assert distance == pytest.approx(85000, abs=5000)

    def test_negative_coordinates(self):
        """Test with negative latitude/longitude."""
        point1 = (-33.8688, 151.2093)  # Sydney
        point2 = (-37.8136, 144.9631)  # Melbourne
        distance = haversine_distance_m(point1, point2)
        # Should be approximately 700km
        assert distance == pytest.approx(700000, abs=10000)

    def test_zero_longitude(self):
        """Test with zero longitude (Greenwich meridian)."""
        point1 = (51.5074, 0.0)  # London
        point2 = (52.5200, 0.0)  # Just north of London
        distance = haversine_distance_m(point1, point2)
        # Should be approximately 111km
        assert distance == pytest.approx(111000, abs=1000)

