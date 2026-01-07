from typing import cast
from uuid import uuid4
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from source.schemas.pydantic.agents import State
from source.api.agents.interactor_abc import AgentsInteractorAbc
from source.config.logging import logger


class AgentsInteractorImpl(AgentsInteractorAbc):
    """
    Реализация оркестратора AI-агентов.
    Управляет выполнением LangGraph с супервизором и специализированными агентами.
    """

    def __init__(self, graph: CompiledStateGraph):
        self._graph = graph

    async def __call__(self, state: State) -> State:
        """
        Выполняет граф агентов и возвращает финальное состояние.
        """
        # Генерируем thread_id для чекпоинтера
        thread_id = str(uuid4())
        config: RunnableConfig = cast(
            RunnableConfig, {"configurable": {"thread_id": thread_id}}
        )

        logger.info(
            f"[AGENTS_INTERACTOR] Starting graph execution for user {state.telegram_user_id}"
        )

        try:
            # Запускаем граф - возвращает dict
            result_raw = await self._graph.ainvoke(input=state, config=config)

            # Преобразуем dict в State
            if isinstance(result_raw, dict):
                result = State(**result_raw)
            else:
                result = result_raw

            logger.info(
                f"[AGENTS_INTERACTOR] Graph execution completed. Result: {result.result[:100] if result.result else 'None'}..."
            )

            return result

        except Exception as e:
            logger.error(f"[AGENTS_INTERACTOR] Graph execution failed: {e}")
            # Возвращаем state с ошибкой
            return state.model_copy(
                update={
                    "result": f"Произошла ошибка при обработке запроса: {str(e)}",
                }
            )
