"""
Тесты для SupervisorServiceImpl.

Используется подход:
- FakeChatModel из langchain для тестирования LLM (не Mock!)
- Реальные промпты
- Фикстуры для State
- Parametrize для разных сценариев
"""

from uuid import uuid4
import pytest
from langchain_core.messages import AIMessage
from langchain_core.language_models.fake_chat_models import FakeChatModel

from source.api.agents.supervisor.service_impl import SupervisorServiceImpl
from source.schemas.pydantic.agents import State, DealData, SupervisorDecision
from source.db.models.choises.enum import TaskTypeChoises
from source.services.prompts.supervisor_prompts import SupervisorPrompts


@pytest.fixture
def supervisor_prompts() -> SupervisorPrompts:
    """Фикстура для создания SupervisorPrompts."""
    return SupervisorPrompts()


@pytest.fixture
def sample_state() -> State:
    """Создает базовое состояние для тестирования."""
    return State(
        telegram_user_id=uuid4(),
        telegram_chat_id=123456,
        crm_user_id=100,
        user_role="manager",
        user_input="Когда погрузка по сделке 1001?",
    )


@pytest.fixture
def state_with_deal() -> State:
    """Состояние с данными о сделке."""
    return State(
        telegram_user_id=uuid4(),
        telegram_chat_id=123456,
        crm_user_id=100,
        user_role="manager",
        user_input="Когда погрузка?",
        deal_data=DealData(
            crm_deal_id=1001,
            status="deal",
            buyer_name="ООО Покупатель",
            total_amount=500000.0,
        ),
    )


@pytest.fixture
def state_with_task_type() -> State:
    """Состояние с уже определенным task_type."""
    return State(
        telegram_user_id=uuid4(),
        telegram_chat_id=123456,
        crm_user_id=100,
        user_role="manager",
        user_input="Подтверди сделку",
        task_type=TaskTypeChoises.confirmation_agent,
    )


class TestSupervisorServiceRouting:
    """Тесты маршрутизации супервизора."""

    async def test_routes_to_reminder_agent(
        self,
        supervisor_prompts: SupervisorPrompts,
        sample_state: State,
    ):
        """Супервизор маршрутизирует на reminder_agent."""
        # FakeChatModel который возвращает структурированный ответ
        fake_llm = FakeChatModel(
            responses=[
                AIMessage(
                    content='{"task_type": "reminder_agent", "reason": "User asks about dates"}'
                )
            ]
        )
        # Создаем structured_llm который возвращает SupervisorDecision
        fake_structured_llm = FakeChatModel(
            responses=[
                SupervisorDecision(
                    task_type=TaskTypeChoises.reminder_agent,
                    reason="User asks about dates",
                )
            ]
        )

        # Переопределяем with_structured_output
        fake_llm.with_structured_output = lambda schema: fake_structured_llm

        supervisor = SupervisorServiceImpl(
            llm=fake_llm, supervisor_prompts=supervisor_prompts
        )

        result_state = await supervisor(state=sample_state)

        assert result_state.task_type == TaskTypeChoises.reminder_agent

    async def test_routes_to_edit_deal_agent(
        self,
        supervisor_prompts: SupervisorPrompts,
    ):
        """Супервизор маршрутизирует на edit_deal_agent."""
        state = State(
            telegram_user_id=uuid4(),
            telegram_chat_id=123456,
            crm_user_id=100,
            user_role="manager",
            user_input="Измени дату погрузки на завтра",
        )

        fake_structured_llm = FakeChatModel(
            responses=[
                SupervisorDecision(
                    task_type=TaskTypeChoises.edit_deal_agent,
                    reason="User wants to edit deal",
                )
            ]
        )
        fake_llm = FakeChatModel(responses=[])
        fake_llm.with_structured_output = lambda schema: fake_structured_llm

        supervisor = SupervisorServiceImpl(
            llm=fake_llm, supervisor_prompts=supervisor_prompts
        )

        result_state = await supervisor(state=state)

        assert result_state.task_type == TaskTypeChoises.edit_deal_agent

    async def test_routes_to_confirmation_agent(
        self,
        supervisor_prompts: SupervisorPrompts,
    ):
        """Супервизор маршрутизирует на confirmation_agent."""
        state = State(
            telegram_user_id=uuid4(),
            telegram_chat_id=123456,
            crm_user_id=100,
            user_role="director",
            user_input="Подтверди сделку 1001",
        )

        fake_structured_llm = FakeChatModel(
            responses=[
                SupervisorDecision(
                    task_type=TaskTypeChoises.confirmation_agent,
                    reason="Director confirmation request",
                )
            ]
        )
        fake_llm = FakeChatModel(responses=[])
        fake_llm.with_structured_output = lambda schema: fake_structured_llm

        supervisor = SupervisorServiceImpl(
            llm=fake_llm, supervisor_prompts=supervisor_prompts
        )

        result_state = await supervisor(state=state)

        assert result_state.task_type == TaskTypeChoises.confirmation_agent

    @pytest.mark.parametrize(
        "task_type",
        [
            TaskTypeChoises.reminder_agent,
            TaskTypeChoises.edit_deal_agent,
            TaskTypeChoises.confirmation_agent,
        ],
    )
    async def test_routes_to_all_agent_types(
        self,
        supervisor_prompts: SupervisorPrompts,
        task_type: TaskTypeChoises,
    ):
        """Проверка маршрутизации на все типы агентов."""
        state = State(
            telegram_user_id=uuid4(),
            telegram_chat_id=123456,
            crm_user_id=100,
            user_role="manager",
            user_input="Test input",
        )

        fake_structured_llm = FakeChatModel(
            responses=[SupervisorDecision(task_type=task_type)]
        )
        fake_llm = FakeChatModel(responses=[])
        fake_llm.with_structured_output = lambda schema: fake_structured_llm

        supervisor = SupervisorServiceImpl(
            llm=fake_llm, supervisor_prompts=supervisor_prompts
        )

        result_state = await supervisor(state=state)

        assert result_state.task_type == task_type


class TestSupervisorServiceStateHandling:
    """Тесты обработки состояния."""

    async def test_preserves_existing_task_type(
        self,
        supervisor_prompts: SupervisorPrompts,
        state_with_task_type: State,
    ):
        """Супервизор не перезаписывает существующий task_type."""
        # LLM не должен вызываться
        fake_llm = FakeChatModel(responses=[])

        supervisor = SupervisorServiceImpl(
            llm=fake_llm, supervisor_prompts=supervisor_prompts
        )

        result_state = await supervisor(state=state_with_task_type)

        # task_type должен остаться прежним
        assert result_state.task_type == TaskTypeChoises.confirmation_agent
        # Остальные поля тоже не должны измениться
        assert result_state.user_input == state_with_task_type.user_input

    async def test_preserves_other_state_fields(
        self,
        supervisor_prompts: SupervisorPrompts,
        state_with_deal: State,
    ):
        """Супервизор сохраняет все остальные поля состояния."""
        fake_structured_llm = FakeChatModel(
            responses=[SupervisorDecision(task_type=TaskTypeChoises.reminder_agent)]
        )
        fake_llm = FakeChatModel(responses=[])
        fake_llm.with_structured_output = lambda schema: fake_structured_llm

        supervisor = SupervisorServiceImpl(
            llm=fake_llm, supervisor_prompts=supervisor_prompts
        )

        result_state = await supervisor(state=state_with_deal)

        # Проверяем что все поля сохранились
        assert result_state.telegram_user_id == state_with_deal.telegram_user_id
        assert result_state.telegram_chat_id == state_with_deal.telegram_chat_id
        assert result_state.user_input == state_with_deal.user_input
        assert result_state.deal_data is not None
        assert result_state.deal_data.crm_deal_id == 1001
        # И добавился task_type
        assert result_state.task_type == TaskTypeChoises.reminder_agent


class TestSupervisorServiceErrorHandling:
    """Тесты обработки ошибок."""

    async def test_fallback_on_llm_error(
        self,
        supervisor_prompts: SupervisorPrompts,
        sample_state: State,
    ):
        """При ошибке LLM используется fallback - reminder_agent."""

        # FakeChatModel который выбрасывает ошибку
        class ErrorLLM(FakeChatModel):
            async def ainvoke(self, input, config=None, **kwargs):
                raise ValueError("LLM API error")

            def with_structured_output(self, schema):
                return self

        error_llm = ErrorLLM(responses=[])

        supervisor = SupervisorServiceImpl(
            llm=error_llm, supervisor_prompts=supervisor_prompts
        )

        result_state = await supervisor(state=sample_state)

        # Должен вернуть fallback - reminder_agent
        assert result_state.task_type == TaskTypeChoises.reminder_agent

    async def test_handles_dict_response(
        self,
        supervisor_prompts: SupervisorPrompts,
        sample_state: State,
    ):
        """Корректно обрабатывает dict ответ от LLM."""
        # FakeChatModel который возвращает dict вместо SupervisorDecision
        fake_structured_llm = FakeChatModel(
            responses=[
                {
                    "task_type": TaskTypeChoises.edit_deal_agent,
                    "reason": "Edit request",
                }
            ]
        )
        fake_llm = FakeChatModel(responses=[])
        fake_llm.with_structured_output = lambda schema: fake_structured_llm

        supervisor = SupervisorServiceImpl(
            llm=fake_llm, supervisor_prompts=supervisor_prompts
        )

        result_state = await supervisor(state=sample_state)

        assert result_state.task_type == TaskTypeChoises.edit_deal_agent
