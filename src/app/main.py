from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.config import Settings
from app.db.connection import create_engine, create_session_factory
from app.routers.errors import register_error_handlers
from app.routers.public.v1.persons.views import router as persons_router


def create_app(settings: Settings | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        config = settings if settings is not None else Settings()
        engine = create_engine(config.DATABASE_URL)
        try:
            application.state.session_factory = create_session_factory(engine)
            yield
        finally:
            await engine.dispose()
            if hasattr(application.state, "session_factory"):
                del application.state.session_factory

    application = FastAPI(
        title="Persons API",
        version="v1",
        lifespan=lifespan,
    )
    register_error_handlers(application)
    application.include_router(persons_router)

    def custom_openapi() -> dict:
        if application.openapi_schema is None:
            schema = get_openapi(
                title=application.title,
                version=application.version,
                openapi_version=application.openapi_version,
                routes=application.routes,
            )
            # RequestValidationError is handled as 400 throughout this app.
            for path in schema["paths"].values():
                for operation in path.values():
                    if isinstance(operation, dict):
                        operation.get("responses", {}).pop("422", None)
            application.openapi_schema = schema
        return application.openapi_schema

    application.openapi = custom_openapi
    return application


app = create_app()
