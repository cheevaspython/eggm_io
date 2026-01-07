from typing import Protocol


class Commiter(Protocol):
    async def commit(self) -> None: ...


class DefaultCommiter(Protocol):
    async def commit(self) -> None: ...
