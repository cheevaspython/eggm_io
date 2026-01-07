from typing import Protocol

from source.schemas.pydantic.agents import State


class ConfirmationAgentServiceAbc(Protocol):
    """
    Protocol для агента подтверждения.
    Отвечает за подтверждение данных сделок и заявок:
    - Запрашивает подтверждение всех полей сделки
    - Фиксирует подтверждения (для руководства)
    - Проверяет корректность данных
    """

    async def __call__(
        self,
        state: State,
    ) -> State:
        """
        Обрабатывает запросы на подтверждение данных.

        Args:
            state: Текущее состояние с данными для подтверждения

        Returns:
            State с результатом обработки и данными для подтверждения
        """
        raise NotImplementedError()
