from typing import Protocol

from source.schemas.pydantic.agents import State


class ReminderAgentServiceAbc(Protocol):
    """
    Protocol для агента напоминаний.
    Отвечает за работу с напоминаниями о важных датах по сделкам:
    - Показывает активные напоминания
    - Предоставляет информацию о предстоящих событиях
    - Отвечает на вопросы о датах сделок
    """

    async def __call__(
        self,
        state: State,
    ) -> State:
        """
        Обрабатывает запросы связанные с напоминаниями.

        Args:
            state: Текущее состояние с запросом пользователя

        Returns:
            State с результатом обработки в поле result
        """
        raise NotImplementedError()
