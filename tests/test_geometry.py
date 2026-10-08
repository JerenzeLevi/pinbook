import pytest

from pinbook.geometry import BoundingBox, haversine_km


def test_haversine_known_distance():
    # Paris -> London is roughly 344 km.
    assert haversine_km(48.8566, 2.3522, 51.5074, -0.1278) == pytest.approx(344, abs=3)


def test_haversine_zero():
    assert haversine_km(10, 20, 10, 20) == 0


def test_box_simple():
    box = BoundingBox.around(0, 0, 111.195)  # about one degree
    assert box.min_lat == pytest.approx(-1, abs=0.01)
    assert len(box.lon_spans) == 1


def test_box_splits_at_antimeridian():
    assert len(BoundingBox.around(0, 179.9, 100).lon_spans) == 2


def test_box_covers_all_longitudes_near_pole():
    assert BoundingBox.around(89.9, 10, 100).lon_spans == ((-180.0, 180.0),)
