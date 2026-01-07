from source.schemas.pydantic.agents import State, AgentType
from source.config.logging import logger


class SupervisorServiceImpl:
    """
    Реализация супервизора.
    Анализирует запрос пользователя и определяет к какому агенту его направить.

    TODO: Интегрировать LLM для умной маршрутизации
    """

    def __init__(self):
        pass

    async def __call__(self, state: State) -> State:
        logger.info("[SUPERVISOR] Analyzing user request for routing")

        user_input = state.user_input or ""
        user_command = state.user_command or ""

        # Простая логика маршрутизации (позже заменим на LLM)
        agent_type = self._determine_agent_type(user_input, user_command)

        logger.info(f"[SUPERVISOR] Routed to agent: {agent_type.value}")

        return state.model_copy(
            update={
                "agent_type": agent_type,
            }
        )

    def _determine_agent_type(
        self,
        user_input: str,
        user_command: str,
    ) -> AgentType:
        """
        Определяет тип агента на основе входных данных.
        Пока простая логика, позже добавим LLM.
        """
        user_input_lower = user_input.lower()

        # Команды
        if user_command in ["/reminders", "/dates"]:
            return AgentType.reminder_agent

        if user_command in ["/confirm", "/check"]:
            return AgentType.confirmation_agent

        if user_command in ["/edit", "/change"]:
            return AgentType.edit_deal_agent

        # Ключевые слова
        reminder_keywords = [
            "напомни",
            "напоминание",
            "дата",
            "когда",
            "срок",
            "погрузка",
            "разгрузка",
            "оплата",
        ]
        if any(keyword in user_input_lower for keyword in reminder_keywords):
            return AgentType.reminder_agent

        confirm_keywords = [
            "подтверд",
            "проверь",
            "верно",
            "правильно",
            "корректно",
        ]
        if any(keyword in user_input_lower for keyword in confirm_keywords):
            return AgentType.confirmation_agent

        edit_keywords = [
            "измени",
            "редактир",
            "поправ",
            "обнови",
            "смени",
        ]
        if any(keyword in user_input_lower for keyword in edit_keywords):
            return AgentType.edit_deal_agent

        # По умолчанию - информационный агент
        return AgentType.info_agent
