"""
Простой Mock для ChatModel для тестирования AI сервисов.
Не используем Mock из unittest - создаем свой класс-заглушку.
"""

from typing import Any, Optional
from langchain_core.messages import AIMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.outputs import ChatResult, ChatGeneration


class SimpleFakeLLM(BaseChatModel):
    """Простой fake LLM который возвращает заранее настроенные ответы."""

    responses: list[str | dict | Any]
    current_index: int = 0

    def __init__(self, responses: list[str | dict | Any]):
        super().__init__(responses=responses, current_index=0)

    def _generate(
        self,
        messages: list,
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Возвращает следующий ответ из списка."""
        if self.current_index >= len(self.responses):
            response = self.responses[-1] if self.responses else "No response"
        else:
            response = self.responses[self.current_index]
            self.current_index += 1

        # Если ответ уже AIMessage, используем его content
        if isinstance(response, AIMessage):
            content = response.content
        # Если ответ dict или объект Pydantic - возвращаем как есть для structured output
        elif isinstance(response, dict) or hasattr(response, "model_dump"):
            content = response
        else:
            content = str(response)

        message = AIMessage(content=content)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    async def _agenerate(
        self,
        messages: list,
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Async версия _generate."""
        return self._generate(messages=messages, stop=stop, run_manager=run_manager, **kwargs)

    @property
    def _llm_type(self) -> str:
        return "simple_fake"


class SimpleFakeStructuredLLM(BaseChatModel):
    """Fake LLM для structured output - возвращает Pydantic объекты."""

    responses: list[Any]
    current_index: int = 0

    def __init__(self, responses: list[Any]):
        super().__init__(responses=responses, current_index=0)

    def _generate(
        self,
        messages: list,
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Возвращает Pydantic объект напрямую."""
        if self.current_index >= len(self.responses):
            response = self.responses[-1] if self.responses else {}
        else:
            response = self.responses[self.current_index]
            self.current_index += 1

        # Для structured output возвращаем объект как есть
        # (SupervisorService преобразует его сам)
        message = AIMessage(content=response)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    async def _agenerate(
        self,
        messages: list,
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Async версия."""
        return self._generate(messages=messages, stop=stop, run_manager=run_manager, **kwargs)

    @property
    def _llm_type(self) -> str:
        return "simple_fake_structured"

    def with_structured_output(self, schema, **kwargs):
        """Возвращает себя - мы уже возвращаем structured output."""
        return self
