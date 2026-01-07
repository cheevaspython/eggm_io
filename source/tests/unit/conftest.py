"""
Conftest для unit тестов.

Упрощенная версия без FastAPI app - только для тестирования Gateway/Service слоев.
"""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from source.db.db_helper import test_db_helper
from source.db.models.base import Base


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """
    Глобальный event loop для всех async тестов.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
async def setup_test_db() -> AsyncGenerator:
    """
    Fixture для настройки тестовой базы данных перед тестами и очистки после.

    Создает и удаляет все таблицы базы данных.
    """
    async with test_db_helper.engine.begin() as conn:
        await conn.run_sync(func=Base.metadata.create_all)

    yield

    async with test_db_helper.engine.begin() as conn:
        await conn.run_sync(func=Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Fixture для создания тестовой сессии базы данных.

    Обеспечивает корректное закрытие сессии после использования.
    """
    async with test_db_helper.session_factory() as session:
        yield session
        await session.close()
