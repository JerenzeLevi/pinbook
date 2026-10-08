import pytest

from tests.conftest import LISBON, MADRID, SINTRA

BASE = "/api/v1/contacts"


async def test_create_normalises_and_returns_metadata(client):
    res = await client.post(BASE, json={**LISBON, "label": "  Lisbon HQ  "})
    assert res.status_code == 201
    body = res.json()
    assert body["label"] == "Lisbon HQ"
    assert body["country_code"] == "PT"
    assert body["created_at"] and body["id"] == 1
    assert res.headers["x-request-id"]


async def test_replace_patch_delete(client):
    cid = (await client.post(BASE, json=LISBON)).json()["id"]

    patched = await client.patch(f"{BASE}/{cid}", json={"city": "Belem"})
    assert patched.json()["city"] == "Belem"
    assert patched.json()["line1"] == LISBON["line1"]

    replaced = await client.put(f"{BASE}/{cid}", json=SINTRA)
    assert replaced.json()["label"] == "Sintra"

    assert (await client.delete(f"{BASE}/{cid}")).status_code == 204
    missing = await client.get(f"{BASE}/{cid}")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "contact_not_found"


@pytest.mark.parametrize(
    "override",
    [
        {"latitude": 90.5},
        {"longitude": -200},
        {"label": "   "},
        {"country_code": "PRT"},
        {"country_code": "1A"},
    ],
)
async def test_validation_rejects_bad_input(client, override):
    assert (await client.post(BASE, json={**LISBON, **override})).status_code == 422


async def test_pagination_is_capped_by_settings(client):
    for payload in (LISBON, SINTRA, MADRID):
        await client.post(BASE, json=payload)
    page = (await client.get(BASE, params={"limit": 50})).json()
    assert page["limit"] == 2 and page["total"] == 3 and len(page["items"]) == 2
    rest = (await client.get(BASE, params={"offset": 2})).json()
    assert [c["label"] for c in rest["items"]] == ["Madrid"]


async def test_nearby_orders_by_distance_and_filters(client):
    for payload in (MADRID, SINTRA, LISBON):
        await client.post(BASE, json=payload)
    res = await client.get(
        f"{BASE}/search/nearby", params={"lat": 38.7223, "lon": -9.1393, "radius_km": 40}
    )
    hits = res.json()
    assert [h["label"] for h in hits] == ["Lisbon HQ", "Sintra"]
    assert hits[0]["distance_km"] == 0
    assert hits[1]["distance_km"] == pytest.approx(23.5, abs=1.5)


async def test_nearby_across_antimeridian(client):
    for label, lon in (("west", 179.9), ("east", -179.9)):
        payload = {**LISBON, "label": label, "latitude": -17.0, "longitude": lon}
        await client.post(BASE, json=payload)
    res = await client.get(
        f"{BASE}/search/nearby", params={"lat": -17.0, "lon": 179.95, "radius_km": 50}
    )
    assert {h["label"] for h in res.json()} == {"west", "east"}


async def test_nearby_rejects_non_positive_radius(client):
    res = await client.get(f"{BASE}/search/nearby", params={"lat": 0, "lon": 0, "radius_km": 0})
    assert res.status_code == 422


async def test_healthz(client):
    assert (await client.get("/healthz")).json() == {"status": "ok"}
