from langchain_openai import ChatOpenAI

from source.schemas.pydantic.agents import State
from source.services.prompts.reminder_prompts import ReminderAgentPrompts
from source.api.agents.reminder.service_abc import ReminderAgentServiceAbc
from source.config.logging import logger


class ReminderAgentServiceImpl(ReminderAgentServiceAbc):
    """
    Агент напоминаний - использует LLM для ответов о датах и сроках сделок.
    """

    def __init__(self, llm: ChatOpenAI, reminder_prompts: ReminderAgentPrompts):
        self._llm = llm
        self._reminder_prompts = reminder_prompts

    async def __call__(self, state: State) -> State:
        logger.info("[REMINDER_AGENT] Processing reminder request")

        prompt = self._reminder_prompts.procedural_reminder_prompt(state=state)
        response = await self._llm.ainvoke(input=prompt)

        # Преобразуем response.content в строку
        if hasattr(response, "content"):
            content = response.content
            result = str(content) if not isinstance(content, str) else content
        else:
            result = str(response)

        logger.info(f"[REMINDER_AGENT] Generated response: {result[:100]}...")

        return state.model_copy(
            update={
                "result": result,
            }
        )
