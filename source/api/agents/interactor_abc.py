from typing import Protocol
from source.schemas.pydantic.agents import State


class AgentsInteractorAbc(Protocol):
    """
    Протокол для оркестратора AI-агентов.
    Управляет выполнением LangGraph и возвращает результат.
    """

    async def __call__(self, state: State) -> State:
        """
        Выполняет граф агентов и возвращает финальное состояние.

        Args:
            state: Начальное состояние с данными пользователя

        Returns:
            Финальное состояние с результатом работы агентов
        """
        ...
