from langchain_openai import ChatOpenAI

from source.schemas.pydantic.agents import State
from source.services.prompts.confirmation_prompts import ConfirmationAgentPrompts
from source.api.agents.confirmation.service_abc import ConfirmationAgentServiceAbc
from source.config.logging import logger


class ConfirmationAgentServiceImpl(ConfirmationAgentServiceAbc):
    """
    Агент подтверждения - использует LLM для запроса и проверки подтверждений данных сделки.
    """

    def __init__(self, llm: ChatOpenAI, confirmation_prompts: ConfirmationAgentPrompts):
        self._llm = llm
        self._confirmation_prompts = confirmation_prompts

    async def __call__(self, state: State) -> State:
        logger.info("[CONFIRMATION_AGENT] Processing confirmation request")

        prompt = self._confirmation_prompts.procedural_confirmation_prompt(state)
        response = await self._llm.ainvoke(prompt)

        # Преобразуем response.content в строку
        if hasattr(response, "content"):
            content = response.content
            result = str(content) if not isinstance(content, str) else content
        else:
            result = str(response)

        logger.info(f"[CONFIRMATION_AGENT] Generated response: {result[:100]}...")

        return state.model_copy(
            update={
                "result": result,
            }
        )
