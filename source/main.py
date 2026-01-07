from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dishka.integrations import fastapi as fastapi_integration

from source.api.routers.http import router as http_router
from source.config.logging import setup_uvicorn_logging
from source.db.db_helper import db_helper
from source.ioc import setup_di
from source.config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await db_helper.dispose()
    await app.state.dishka_container.close()


def create_app() -> FastAPI:
    container = setup_di()
    setup_uvicorn_logging()

    app = FastAPI(
        root_path=settings.names.path,
        title=settings.names.title,
        lifespan=lifespan,
        default_response_class=ORJSONResponse,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.middleware.cors_origins,
        allow_credentials=True,
        allow_methods=settings.middleware.allow_methods,
        allow_headers=settings.middleware.allow_headers,
    )

    app.include_router(router=http_router)
    fastapi_integration.setup_dishka(container=container, app=app)

    return app
