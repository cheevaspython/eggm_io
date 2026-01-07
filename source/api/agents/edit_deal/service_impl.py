from langchain_openai import ChatOpenAI

from source.schemas.pydantic.agents import State
from source.services.prompts.edit_deal_prompts import EditDealAgentPrompts
from source.api.agents.edit_deal.service_abc import EditDealAgentServiceAbc
from source.config.logging import logger


class EditDealAgentServiceImpl(EditDealAgentServiceAbc):
    """
    Агент редактирования сделок - использует LLM для помощи в редактировании полей сделки.
    """

    def __init__(self, llm: ChatOpenAI, edit_deal_prompts: EditDealAgentPrompts):
        self._llm = llm
        self._edit_deal_prompts = edit_deal_prompts

    async def __call__(self, state: State) -> State:
        logger.info("[EDIT_DEAL_AGENT] Processing edit request")

        prompt = self._edit_deal_prompts.procedural_edit_deal_prompt(state)
        response = await self._llm.ainvoke(prompt)

        # Преобразуем response.content в строку
        if hasattr(response, "content"):
            content = response.content
            result = str(content) if not isinstance(content, str) else content
        else:
            result = str(response)

        logger.info(f"[EDIT_DEAL_AGENT] Generated response: {result[:100]}...")

        return state.model_copy(
            update={
                "result": result,
            }
        )
