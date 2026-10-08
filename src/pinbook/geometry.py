"""Spherical geometry helpers for proximity search."""
from dataclasses import dataclass
from math import asin, cos, degrees, radians, sin, sqrt

EARTH_RADIUS_KM = 6371.0088
_WHOLE_WORLD = ((-180.0, 180.0),)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two WGS 84 points, in kilometres."""
    phi1, phi2 = radians(lat1), radians(lat2)
    a = sin((phi2 - phi1) / 2) ** 2 + cos(phi1) * cos(phi2) * sin(radians(lon2 - lon1) / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(min(1.0, sqrt(a)))


@dataclass(frozen=True)
class BoundingBox:
    """A latitude band plus one or two longitude spans that enclose a search circle.

    Two longitude spans are produced when the circle crosses the antimeridian.
    """

    min_lat: float
    max_lat: float
    lon_spans: tuple[tuple[float, float], ...]

    @classmethod
    def around(cls, lat: float, lon: float, radius_km: float) -> "BoundingBox":
        angular = radius_km / EARTH_RADIUS_KM  # radius as an angle at the Earth's centre
        min_lat = max(lat - degrees(angular), -90.0)
        max_lat = min(lat + degrees(angular), 90.0)

        # A circle covering a pole touches every meridian.
        if lat + degrees(angular) >= 90.0 or lat - degrees(angular) <= -90.0:
            return cls(min_lat, max_lat, _WHOLE_WORLD)

        ratio = sin(angular) / cos(radians(lat))
        if ratio >= 1.0:
            return cls(min_lat, max_lat, _WHOLE_WORLD)

        delta = degrees(asin(ratio))
        low, high = lon - delta, lon + delta
        if low < -180.0:
            spans = ((low + 360.0, 180.0), (-180.0, high))
        elif high > 180.0:
            spans = ((low, 180.0), (-180.0, high - 360.0))
        else:
            spans = ((low, high),)
        return cls(min_lat, max_lat, spans)
