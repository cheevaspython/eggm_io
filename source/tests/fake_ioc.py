from typing import AsyncGenerator

from dishka import provide, Scope
from sqlalchemy.ext.asyncio import AsyncSession

from source.ioc import AppProvider


class _TestProvider(AppProvider):
    def __init__(self, test_session: AsyncSession):
        super().__init__()
        self._test_session = test_session

    @provide(scope=Scope.REQUEST)
    async def provide_session(self) -> AsyncGenerator[AsyncSession, None]:
        yield self._test_session
