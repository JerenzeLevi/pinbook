# Pinbook

Pinbook is a small HTTP service that stores contact addresses together with their map coordinates and answers one question quickly: *which of my contacts are within X kilometres of here?*

It is built on FastAPI with a fully asynchronous stack (SQLAlchemy 2.0 + aiosqlite), so it needs no external database and runs from a single command.

## Highlights

- **Versioned REST API** under `/api/v1`, with interactive docs at `/docs`.
- **Full and partial updates**: `PUT` replaces a contact, `PATCH` changes only the fields you send.
- **Strict validation**: coordinate ranges, trimmed non-empty text, and ISO 3166-1 alpha-2 country codes (normalised to upper case).
- **Proximity search** with a bounding-box prefilter in SQL and exact great-circle (haversine) distances; correct across the antimeridian and near the poles.
- **Paginated listing** with a configurable page-size cap.
- **Consistent error envelope**: `{"error": {"code": ..., "message": ...}}`.
- **Observability basics**: an `X-Request-ID` header on every response and one structured access-log line per request.
- **Tested and linted**: pytest (async) and ruff, run on every push by GitHub Actions.

## Quick start

Requires Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn pinbook.main:app --reload
```

Open <http://127.0.0.1:8000/docs>. The SQLite file `pinbook.db` is created on first start.

Run the checks:

```bash
ruff check .
pytest
```

## Using the API

```bash
# create
curl -X POST http://127.0.0.1:8000/api/v1/contacts -H "Content-Type: application/json" -d '{
  "label": "Warehouse", "line1": "12 Harbour Road", "city": "Lisbon",
  "country_code": "PT", "latitude": 38.7223, "longitude": -9.1393 }'

# contacts within 40 km of a point, nearest first
curl "http://127.0.0.1:8000/api/v1/contacts/search/nearby?lat=38.72&lon=-9.14&radius_km=40"
```

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/contacts` | Create a contact |
| `GET` | `/api/v1/contacts` | List contacts (`limit`, `offset`) |
| `GET` | `/api/v1/contacts/{id}` | Fetch one contact |
| `PUT` | `/api/v1/contacts/{id}` | Replace a contact |
| `PATCH` | `/api/v1/contacts/{id}` | Update selected fields |
| `DELETE` | `/api/v1/contacts/{id}` | Remove a contact |
| `GET` | `/api/v1/contacts/search/nearby` | Proximity search (`lat`, `lon`, `radius_km`, `limit`) |
| `GET` | `/healthz` | Liveness check |

## Configuration

Settings are read from environment variables prefixed with `PINBOOK_` (or from a `.env` file).

| Variable | Default | Meaning |
|---|---|---|
| `PINBOOK_DATABASE_URL` | `sqlite+aiosqlite:///./pinbook.db` | Async SQLAlchemy URL |
| `PINBOOK_LOG_LEVEL` | `INFO` | Logging level |
| `PINBOOK_MAX_PAGE_SIZE` | `100` | Upper bound for `limit` on listings |
| `PINBOOK_MAX_SEARCH_RADIUS_KM` | `2000` | Upper bound for `radius_km` |

## Layout

```
src/pinbook/
├── main.py          application factory, lifespan, access-log middleware
├── settings.py      environment-driven configuration
├── db.py            engine and session factory
├── models.py        ORM model
├── schemas.py       request/response models and validation
├── repository.py    persistence and proximity query
├── geometry.py      haversine distance and bounding boxes
├── errors.py        domain errors mapped to HTTP responses
└── api/
    ├── deps.py      dependency providers
    └── v1/contacts.py
tests/               API tests and geometry unit tests
```

## Design notes

- **Application factory.** `create_app(settings)` builds an isolated app per call, so tests run against a throwaway database without monkeypatching.
- **Repository layer.** Route handlers stay thin; each repository method is one atomic unit of work, and timestamps are re-read from the database after writes.
- **Proximity search.** Candidates are narrowed with an indexed latitude/longitude box, then filtered by exact distance. The box splits in two when the search circle crosses ±180° longitude.
- **Growth path.** SQLite keeps setup trivial. Moving to PostgreSQL (and PostGIS for spatial indexing) needs only a different `PINBOOK_DATABASE_URL` driver plus a swap of the box query.
