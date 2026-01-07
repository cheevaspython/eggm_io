"""
Тесты для ConfirmationAgentServiceImpl.

Используется подход:
- SimpleFakeLLM (свой Mock класс)
- Реальные промпты
- Фикстуры для State
"""

from uuid import uuid4
import pytest

from source.tests.unit.fake_llm import SimpleFakeLLM
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


class TestConfirmationAgentServiceBasic:
    """Базовые тесты ConfirmationAgentService."""

    async def test_returns_confirmation_response(
        self,
        confirmation_prompts: ConfirmationAgentPrompts,
        state_manager_confirmation: State,
    ):
        """Агент возвращает ответ о подтверждении."""
        fake_llm = SimpleFakeLLM(
            responses=["Сделка 1001 успешно подтверждена менеджером"]
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
        fake_llm = SimpleFakeLLM(responses=["Подтверждение успешно"])

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

    @pytest.mark.parametrize(
        "user_role,response",
        [
            ("manager", "Подтверждено менеджером"),
            ("director", "Подтверждено директором"),
        ],
    )
    async def test_different_roles_confirmation(
        self,
        confirmation_prompts: ConfirmationAgentPrompts,
        user_role: str,
        response: str,
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

        fake_llm = SimpleFakeLLM(responses=[response])

        confirmation_agent = ConfirmationAgentServiceImpl(
            llm=fake_llm, confirmation_prompts=confirmation_prompts
        )

        result_state = await confirmation_agent(state=state)

        assert result_state.result == response
