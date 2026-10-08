"""Application factory."""
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request

from pinbook import models  # noqa: F401  (registers tables on Base.metadata)
from pinbook.api.v1 import contacts
from pinbook.db import Base, build_engine, build_sessionmaker
from pinbook.errors import register_error_handlers
from pinbook.settings import Settings, get_settings

logger = logging.getLogger("pinbook")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(
        level=settings.log_level.upper(), format="%(asctime)s %(levelname)-7s %(name)s: %(message)s"
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = build_engine(settings.database_url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        app.state.settings = settings
        app.state.sessionmaker = build_sessionmaker(engine)
        logger.info("pinbook ready (db=%s)", settings.database_url)
        yield
        await engine.dispose()

    app = FastAPI(
        title="Pinbook",
        summary="Contact addresses pinned to the map, with proximity search.",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def access_log(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        logger.info(
            "[%s] %s %s %d %.1fms",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            (time.perf_counter() - started) * 1000,
        )
        return response

    api_v1 = APIRouter(prefix="/api/v1")
    api_v1.include_router(contacts.router)
    app.include_router(api_v1)

    @app.get("/healthz", tags=["meta"])
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    register_error_handlers(app)
    return app


app = create_app()
