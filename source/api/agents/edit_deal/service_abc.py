from typing import Protocol

from source.schemas.pydantic.agents import State


class EditDealAgentServiceAbc(Protocol):
    """
    Protocol для агента редактирования сделок.
    Отвечает за редактирование полей сделок и заявок:
    - Изменение дат (погрузка, разгрузка, оплата)
    - Изменение сумм и условий
    - Изменение клиентов и контактных данных
    - Синхронизация изменений с CRM через API
    """

    async def __call__(
        self,
        state: State,
    ) -> State:
        """
        Обрабатывает запросы на редактирование данных сделки.

        Args:
            state: Текущее состояние с запросом на редактирование

        Returns:
            State с результатом редактирования
        """
        raise NotImplementedError()
