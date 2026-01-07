from source.schemas.pydantic.agents import State


class SupervisorPrompts:
    @staticmethod
    def procedural_supervisor_prompt(state: State) -> str:
        """
        Промпт для супервизора - определение к какому агенту направить запрос
        """
        return (
            "Ты супервизор, который распределяет задачи между агентами.\n"
            "Определи, к какому агенту направить запрос пользователя.\n\n"
            "Правила:\n"
            "- Если task_type уже заполнен, не меняй его и верни без изменений.\n"
            "- Если запрос о напоминаниях, датах, сроках → reminder_agent\n"
            "- Если запрос о подтверждении данных, проверке корректности → confirm_agent\n"
            "- Если запрос об изменении, редактировании данных → edit_deal_agent\n"
            "- По умолчанию → reminder_agent\n\n"
            f"task_type='{state.task_type}'\n"
            f"user_input='{state.user_input}'\n"
            f"user_command='{state.user_command}'\n"
        )
