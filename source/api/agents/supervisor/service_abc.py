from typing import Protocol

from source.schemas.pydantic.agents import State


class SupervisorServiceAbc(Protocol):
    """
    Protocol для супервизора.
    Супервизор отвечает за маршрутизацию запросов к специализированным агентам.
    """

    async def __call__(
        self,
        state: State,
    ) -> State:
        """
        Анализирует входящий запрос и определяет какой агент должен его обработать.

        Args:
            state: Текущее состояние с пользовательским запросом

        Returns:
            State с установленным agent_type для маршрутизации
        """
        raise NotImplementedError()
