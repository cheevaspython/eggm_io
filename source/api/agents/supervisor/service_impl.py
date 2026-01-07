from source.schemas.pydantic.agents import State
from source.db.models.choises.enum import TaskTypeChoises
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
        task_type = self._determine_task_type(user_input, user_command)

        logger.info(f"[SUPERVISOR] Routed to agent: {task_type.value}")

        return state.model_copy(
            update={
                "task_type": task_type,
            }
        )

    def _determine_task_type(
        self,
        user_input: str,
        user_command: str,
    ) -> TaskTypeChoises:
        """
        Определяет тип задачи на основе входных данных.
        Пока простая логика, позже добавим LLM.
        """
        user_input_lower = user_input.lower()

        # Команды
        if user_command in ["/reminders", "/dates"]:
            return TaskTypeChoises.reminder_agent

        if user_command in ["/confirm", "/check"]:
            return TaskTypeChoises.confirm_agent

        if user_command in ["/edit", "/change"]:
            return TaskTypeChoises.edit_deal_agent

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
            return TaskTypeChoises.reminder_agent

        confirm_keywords = [
            "подтверд",
            "проверь",
            "верно",
            "правильно",
            "корректно",
        ]
        if any(keyword in user_input_lower for keyword in confirm_keywords):
            return TaskTypeChoises.confirm_agent

        edit_keywords = [
            "измени",
            "редактир",
            "поправ",
            "обнови",
            "смени",
        ]
        if any(keyword in user_input_lower for keyword in edit_keywords):
            return TaskTypeChoises.edit_deal_agent

        # По умолчанию - агент напоминаний
        return TaskTypeChoises.reminder_agent
