"""
Тесты для ConfirmationAgentServiceImpl.

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

from source.api.agents.confirmation.service_impl import ConfirmationAgentServiceImpl
from source.schemas.pydantic.agents import State, DealData
from source.services.prompts.confirmation_prompts import ConfirmationAgentPrompts


@pytest.fixture
def confirmation_prompts() -> ConfirmationAgentPrompts:
    """Фикстура для создания ConfirmationAgentPrompts."""
    return ConfirmationAgentPrompts()


@pytest.fixture
def state_manager_confirmation() -> State:
    """Менеджер подтверждает сделку."""
    return State(
        telegram_user_id=uuid4(),
        telegram_chat_id=123456,
        crm_user_id=100,
        user_role="manager",
        user_input="Подтверждаю сделку 1001",
        deal_data=DealData(
            crm_deal_id=1001,
            status="calculation",
            buyer_name="ООО Покупатель",
            total_amount=500000.0,
            is_confirmed_by_manager=False,
            is_confirmed_by_director=False,
        ),
    )


@pytest.fixture
def state_director_confirmation() -> State:
    """Директор подтверждает сделку."""
    return State(
        telegram_user_id=uuid4(),
        telegram_chat_id=789012,
        crm_user_id=200,
        user_role="director",
        user_input="Подтверждаю сделку 1001",
        deal_data=DealData(
            crm_deal_id=1001,
            status="confirmed_calculation",
            buyer_name="ООО Покупатель",
            total_amount=500000.0,
            is_confirmed_by_manager=True,
            is_confirmed_by_director=False,
        ),
    )


@pytest.fixture
def state_already_confirmed() -> State:
    """Сделка уже подтверждена."""
    return State(
        telegram_user_id=uuid4(),
        telegram_chat_id=123456,
        crm_user_id=100,
        user_role="manager",
        user_input="Статус сделки 1001",
        deal_data=DealData(
            crm_deal_id=1001,
            status="deal",
            buyer_name="ООО Покупатель",
            is_confirmed_by_manager=True,
            is_confirmed_by_director=True,
        ),
    )


class TestConfirmationAgentServiceBasic:
    """Базовые тесты ConfirmationAgentService."""

    async def test_returns_confirmation_response(
        self,
        confirmation_prompts: ConfirmationAgentPrompts,
        state_manager_confirmation: State,
    ):
        """Агент возвращает ответ о подтверждении."""
        fake_llm = FakeChatModel(
            responses=[
                AIMessage(content="Сделка 1001 успешно подтверждена менеджером")
            ]
        )

        confirmation_agent = ConfirmationAgentServiceImpl(
            llm=fake_llm, confirmation_prompts=confirmation_prompts
        )

        result_state = await confirmation_agent(state=state_manager_confirmation)

        assert result_state.result is not None
        assert "подтверждена" in result_state.result.lower()
        assert "1001" in result_state.result

    async def test_preserves_state_fields(
        self,
        confirmation_prompts: ConfirmationAgentPrompts,
        state_manager_confirmation: State,
    ):
        """Агент сохраняет все поля состояния."""
        fake_llm = FakeChatModel(
            responses=[AIMessage(content="Подтверждение успешно")]
        )

        confirmation_agent = ConfirmationAgentServiceImpl(
            llm=fake_llm, confirmation_prompts=confirmation_prompts
        )

        result_state = await confirmation_agent(state=state_manager_confirmation)

        # Все исходные поля сохранились
        assert (
            result_state.telegram_user_id
            == state_manager_confirmation.telegram_user_id
        )
        assert result_state.user_input == state_manager_confirmation.user_input
        assert result_state.user_role == "manager"
        assert result_state.deal_data is not None
        assert result_state.deal_data.crm_deal_id == 1001
        # И добавился result
        assert result_state.result is not None

    async def test_converts_response_to_string(
        self,
        confirmation_prompts: ConfirmationAgentPrompts,
        state_manager_confirmation: State,
    ):
        """Агент корректно преобразует ответ в строку."""
        fake_llm = FakeChatModel(
            responses=[AIMessage(content="Подтверждение обработано")]
        )

        confirmation_agent = ConfirmationAgentServiceImpl(
            llm=fake_llm, confirmation_prompts=confirmation_prompts
        )

        result_state = await confirmation_agent(state=state_manager_confirmation)

        assert isinstance(result_state.result, str)
        assert result_state.result == "Подтверждение обработано"


class TestConfirmationAgentServiceScenarios:
    """Тесты различных сценариев подтверждения."""

    async def test_manager_confirms_deal(
        self,
        confirmation_prompts: ConfirmationAgentPrompts,
        state_manager_confirmation: State,
    ):
        """Менеджер подтверждает сделку."""
        fake_llm = FakeChatModel(
            responses=[
                AIMessage(
                    content="Сделка 1001 подтверждена менеджером. Ожидается подтверждение директора."
                )
            ]
        )

        confirmation_agent = ConfirmationAgentServiceImpl(
            llm=fake_llm, confirmation_prompts=confirmation_prompts
        )

        result_state = await confirmation_agent(state=state_manager_confirmation)

        assert "менеджером" in result_state.result.lower()
        assert "директора" in result_state.result.lower()

    async def test_director_confirms_deal(
        self,
        confirmation_prompts: ConfirmationAgentPrompts,
        state_director_confirmation: State,
    ):
        """Директор подтверждает сделку."""
        fake_llm = FakeChatModel(
            responses=[
                AIMessage(content="Сделка 1001 полностью подтверждена директором")
            ]
        )

        confirmation_agent = ConfirmationAgentServiceImpl(
            llm=fake_llm, confirmation_prompts=confirmation_prompts
        )

        result_state = await confirmation_agent(state=state_director_confirmation)

        assert "директором" in result_state.result.lower()
        assert "подтверждена" in result_state.result.lower()

    async def test_already_confirmed_deal(
        self,
        confirmation_prompts: ConfirmationAgentPrompts,
        state_already_confirmed: State,
    ):
        """Проверка уже подтвержденной сделки."""
        fake_llm = FakeChatModel(
            responses=[
                AIMessage(
                    content="Сделка 1001 уже подтверждена менеджером и директором"
                )
            ]
        )

        confirmation_agent = ConfirmationAgentServiceImpl(
            llm=fake_llm, confirmation_prompts=confirmation_prompts
        )

        result_state = await confirmation_agent(state=state_already_confirmed)

        assert "уже подтверждена" in result_state.result.lower()

    @pytest.mark.parametrize(
        "user_role,expected_keyword",
        [
            ("manager", "менеджер"),
            ("director", "директор"),
        ],
    )
    async def test_different_roles_confirmation(
        self,
        confirmation_prompts: ConfirmationAgentPrompts,
        user_role: str,
        expected_keyword: str,
    ):
        """Проверка подтверждений от разных ролей."""
        state = State(
            telegram_user_id=uuid4(),
            telegram_chat_id=123456,
            crm_user_id=100,
            user_role=user_role,
            user_input="Подтверждаю сделку",
            deal_data=DealData(
                crm_deal_id=2001,
                status="calculation",
                buyer_name="Тест",
            ),
        )

        fake_llm = FakeChatModel(
            responses=[AIMessage(content=f"Подтверждено {expected_keyword}ом")]
        )

        confirmation_agent = ConfirmationAgentServiceImpl(
            llm=fake_llm, confirmation_prompts=confirmation_prompts
        )

        result_state = await confirmation_agent(state=state)

        assert expected_keyword in result_state.result.lower()


class TestConfirmationAgentServiceResponseHandling:
    """Тесты обработки различных форматов ответов."""

    async def test_handles_string_content(
        self,
        confirmation_prompts: ConfirmationAgentPrompts,
        state_manager_confirmation: State,
    ):
        """Обработка строкового content."""
        fake_llm = FakeChatModel(responses=[AIMessage(content="Успешно подтверждено")])

        confirmation_agent = ConfirmationAgentServiceImpl(
            llm=fake_llm, confirmation_prompts=confirmation_prompts
        )

        result_state = await confirmation_agent(state=state_manager_confirmation)

        assert result_state.result == "Успешно подтверждено"

    async def test_handles_multiline_response(
        self,
        confirmation_prompts: ConfirmationAgentPrompts,
        state_manager_confirmation: State,
    ):
        """Обработка многострочного ответа."""
        multiline_response = """Сделка 1001 подтверждена менеджером.

        Статус:
        - Менеджер: ✓
        - Директор: ожидается

        Следующий шаг: подтверждение директора"""

        fake_llm = FakeChatModel(responses=[AIMessage(content=multiline_response)])

        confirmation_agent = ConfirmationAgentServiceImpl(
            llm=fake_llm, confirmation_prompts=confirmation_prompts
        )

        result_state = await confirmation_agent(state=state_manager_confirmation)

        assert result_state.result == multiline_response
        assert "Менеджер: ✓" in result_state.result

    async def test_handles_confirmation_details(
        self,
        confirmation_prompts: ConfirmationAgentPrompts,
    ):
        """Обработка детального ответа о подтверждении."""
        state = State(
            telegram_user_id=uuid4(),
            telegram_chat_id=123456,
            crm_user_id=100,
            user_role="director",
            user_input="Подтверди сделку 3001 на сумму 1млн",
            deal_data=DealData(
                crm_deal_id=3001,
                status="confirmed_calculation",
                buyer_name="ООО Большой Покупатель",
                total_amount=1000000.0,
                is_confirmed_by_manager=True,
            ),
        )

        detailed_response = """Подтверждаю сделку 3001:
        - Покупатель: ООО Большой Покупатель
        - Сумма: 1 000 000 руб
        - Статус: Полностью подтверждено"""

        fake_llm = FakeChatModel(responses=[AIMessage(content=detailed_response)])

        confirmation_agent = ConfirmationAgentServiceImpl(
            llm=fake_llm, confirmation_prompts=confirmation_prompts
        )

        result_state = await confirmation_agent(state=state)

        assert "3001" in result_state.result
        assert "1 000 000" in result_state.result
