import httpx
import pytest

from pinbook.main import create_app
from pinbook.settings import Settings

LISBON = {
    "label": "Lisbon HQ", "line1": "12 Harbour Road", "city": "Lisbon",
    "country_code": "pt", "latitude": 38.7223, "longitude": -9.1393,
}
SINTRA = {**LISBON, "label": "Sintra", "city": "Sintra", "latitude": 38.8029, "longitude": -9.3817}
MADRID = {**LISBON, "label": "Madrid", "city": "Madrid", "country_code": "ES",
          "latitude": 40.4168, "longitude": -3.7038}


@pytest.fixture
async def client(tmp_path):
    settings = Settings(database_url=f"sqlite+aiosqlite:///{tmp_path / 'test.db'}", max_page_size=2)
    app = create_app(settings)
    # httpx's ASGI transport does not run lifespan events, so drive them explicitly.
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as http:
            yield http
