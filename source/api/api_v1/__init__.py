from fastapi import APIRouter

from source.config.settings import settings
from source.api.api_v1.views.healthz import router as health_router

public_router = APIRouter(
    prefix=settings.api.v1.prefix,
)
public_router.include_router(router=health_router)
