"""
Тесты для AgentsInteractorImpl.

Используется подход:
- Свой FakeGraph (простой класс-заглушка для CompiledStateGraph)
- Фикстуры для State
"""

from uuid import uuid4
import pytest

from source.api.agents.interactor_impl import AgentsInteractorImpl
from source.schemas.pydantic.agents import State


class FakeGraph:
    """Простая заглушка для CompiledStateGraph."""

    def __init__(self, return_value: State | dict | Exception):
        self.return_value = return_value
        self.calls = []

    async def ainvoke(self, input, config):
        """Сохраняет вызов и возвращает настроенное значение."""
        self.calls.append({"input": input, "config": config})

        if isinstance(self.return_value, Exception):
            raise self.return_value

        return self.return_value


@pytest.fixture
def sample_state() -> State:
    """Создает базовое состояние для тестирования."""
    return State(
        telegram_user_id=uuid4(),
        telegram_chat_id=123456,
        crm_user_id=100,
        user_role="manager",
        user_input="Когда погрузка?",
    )


class TestAgentsInteractorBasic:
    """Базовые тесты AgentsInteractor."""

    async def test_executes_graph_and_returns_state(
        self,
        sample_state: State,
    ):
        """Interactor выполняет граф и возвращает результат."""
        result_state = sample_state.model_copy(
            update={"result": "Погрузка завтра"}
        )
        fake_graph = FakeGraph(return_value=result_state)

        interactor = AgentsInteractorImpl(graph=fake_graph)

        result = await interactor(state=sample_state)

        assert result.result == "Погрузка завтра"
        assert result.telegram_user_id == sample_state.telegram_user_id
        assert len(fake_graph.calls) == 1

    async def test_converts_dict_to_state(
        self,
        sample_state: State,
    ):
        """Interactor преобразует dict ответ в State."""
        # Граф возвращает dict
        result_dict = {
            "telegram_user_id": sample_state.telegram_user_id,
            "telegram_chat_id": sample_state.telegram_chat_id,
            "crm_user_id": sample_state.crm_user_id,
            "user_role": sample_state.user_role,
            "user_input": sample_state.user_input,
            "result": "Ответ от графа",
        }
        fake_graph = FakeGraph(return_value=result_dict)

        interactor = AgentsInteractorImpl(graph=fake_graph)

        result = await interactor(state=sample_state)

        assert isinstance(result, State)
        assert result.result == "Ответ от графа"

    async def test_passes_config_to_graph(
        self,
        sample_state: State,
    ):
        """Interactor передает config с thread_id в граф."""
        result_state = sample_state.model_copy(update={"result": "OK"})
        fake_graph = FakeGraph(return_value=result_state)

        interactor = AgentsInteractorImpl(graph=fake_graph)

        await interactor(state=sample_state)

        # Проверяем что был передан config с thread_id
        assert len(fake_graph.calls) == 1
        config = fake_graph.calls[0]["config"]
        assert "configurable" in config
        assert "thread_id" in config["configurable"]


class TestAgentsInteractorErrorHandling:
    """Тесты обработки ошибок."""

    async def test_handles_graph_error(
        self,
        sample_state: State,
    ):
        """При ошибке графа возвращает state с сообщением об ошибке."""
        fake_graph = FakeGraph(return_value=ValueError("Graph execution failed"))

        interactor = AgentsInteractorImpl(graph=fake_graph)

        result = await interactor(state=sample_state)

        assert result.result is not None
        assert "ошибка" in result.result.lower()
        assert "Graph execution failed" in result.result

    async def test_preserves_original_state_on_error(
        self,
        sample_state: State,
    ):
        """При ошибке сохраняет все поля исходного state."""
        fake_graph = FakeGraph(return_value=RuntimeError("Test error"))

        interactor = AgentsInteractorImpl(graph=fake_graph)

        result = await interactor(state=sample_state)

        # Все исходные поля должны быть сохранены
        assert result.telegram_user_id == sample_state.telegram_user_id
        assert result.telegram_chat_id == sample_state.telegram_chat_id
        assert result.crm_user_id == sample_state.crm_user_id
        assert result.user_input == sample_state.user_input
        # Только result добавлен с ошибкой
        assert result.result is not None
        assert "ошибка" in result.result.lower()
