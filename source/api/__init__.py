from fastapi import APIRouter

from source.config.settings import settings
from source.api.api_v1 import public_router

router = APIRouter(
    prefix=settings.api.prefix,
)
router.include_router(public_router)
