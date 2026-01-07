from langchain_openai import ChatOpenAI

from source.schemas.pydantic.agents import State, SupervisorDecision
from source.db.models.choises.enum import TaskTypeChoises
from source.services.prompts.supervisor_prompts import SupervisorPrompts
from source.config.logging import logger


class SupervisorServiceImpl:
    """
    Реализация супервизора.
    Использует LLM для анализа запроса пользователя и определения агента для маршрутизации.
    """

    def __init__(self, llm: ChatOpenAI, supervisor_prompts: SupervisorPrompts):
        self._llm = llm
        self._supervisor_prompts = supervisor_prompts
        self._structured_llm = llm.with_structured_output(SupervisorDecision)

    async def __call__(self, state: State) -> State:
        logger.info("[SUPERVISOR] Analyzing user request for routing")

        # Если task_type уже определен (например, через команду), оставляем как есть
        if state.task_type:
            logger.info(f"[SUPERVISOR] Task type already set: {state.task_type.value}")
            return state

        # Используем LLM для определения task_type
        prompt = self._supervisor_prompts.procedural_supervisor_prompt(state)

        try:
            decision = await self._structured_llm.ainvoke(prompt)
            task_type = decision.task_type

            logger.info(
                f"[SUPERVISOR] Routed to agent: {task_type.value}"
                + (f" (reason: {decision.reason})" if decision.reason else "")
            )

            return state.model_copy(
                update={
                    "task_type": task_type,
                }
            )
        except Exception as e:
            logger.error(
                f"[SUPERVISOR] LLM routing failed: {e}, falling back to default"
            )
            # Fallback к reminder_agent при ошибке
            return state.model_copy(
                update={
                    "task_type": TaskTypeChoises.reminder_agent,
                }
            )
