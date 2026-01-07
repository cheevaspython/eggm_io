"""
Тесты для EditDealAgentServiceImpl.

Используется подход:
- SimpleFakeLLM (свой Mock класс)
- Реальные промпты
- Фикстуры для State
"""

from uuid import uuid4
from datetime import datetime, timezone, timedelta
import pytest

from source.tests.unit.fake_llm import SimpleFakeLLM
from source.api.agents.edit_deal.service_impl import EditDealAgentServiceImpl
from source.schemas.pydantic.agents import State, DealData
from source.services.prompts.edit_deal_prompts import EditDealAgentPrompts


@pytest.fixture
def edit_deal_prompts() -> EditDealAgentPrompts:
    """Фикстура для создания EditDealAgentPrompts."""
    return EditDealAgentPrompts()


@pytest.fixture
def state_edit_loading_date() -> State:
    """Запрос на изменение даты погрузки."""
    now = datetime.now(timezone.utc)
    return State(
        telegram_user_id=uuid4(),
        telegram_chat_id=123456,
        crm_user_id=100,
        user_role="manager",
        user_input="Измени дату погрузки на 20 января",
        deal_data=DealData(
            crm_deal_id=1001,
            status="deal",
            buyer_name="ООО Покупатель",
            total_amount=500000.0,
            loading_date=now + timedelta(days=5),
        ),
    )


class TestEditDealAgentServiceBasic:
    """Базовые тесты EditDealAgentService."""

    async def test_returns_edit_response(
        self,
        edit_deal_prompts: EditDealAgentPrompts,
        state_edit_loading_date: State,
    ):
        """Агент возвращает ответ об изменении."""
        fake_llm = SimpleFakeLLM(
            responses=["Дата погрузки по сделке 1001 изменена на 20 января"]
        )

        edit_deal_agent = EditDealAgentServiceImpl(
            llm=fake_llm, edit_deal_prompts=edit_deal_prompts
        )

        result_state = await edit_deal_agent(state=state_edit_loading_date)

        assert result_state.result is not None
        assert "изменена" in result_state.result.lower()
        assert "1001" in result_state.result

    async def test_preserves_state_fields(
        self,
        edit_deal_prompts: EditDealAgentPrompts,
        state_edit_loading_date: State,
    ):
        """Агент сохраняет все поля состояния."""
        fake_llm = SimpleFakeLLM(responses=["Изменение успешно применено"])

        edit_deal_agent = EditDealAgentServiceImpl(
            llm=fake_llm, edit_deal_prompts=edit_deal_prompts
        )

        result_state = await edit_deal_agent(state=state_edit_loading_date)

        # Все исходные поля сохранились
        assert result_state.telegram_user_id == state_edit_loading_date.telegram_user_id
        assert result_state.user_input == state_edit_loading_date.user_input
        assert result_state.deal_data is not None
        assert result_state.deal_data.crm_deal_id == 1001
        # И добавился result
        assert result_state.result is not None

    @pytest.mark.parametrize(
        "edit_request,response",
        [
            ("Измени дату погрузки", "Дата погрузки изменена"),
            ("Измени сумму", "Сумма обновлена"),
            ("Измени покупателя", "Покупатель изменен"),
        ],
    )
    async def test_different_field_edits(
        self,
        edit_deal_prompts: EditDealAgentPrompts,
        edit_request: str,
        response: str,
    ):
        """Проверка редактирования разных полей."""
        state = State(
            telegram_user_id=uuid4(),
            telegram_chat_id=123456,
            crm_user_id=100,
            user_role="manager",
            user_input=edit_request,
            deal_data=DealData(
                crm_deal_id=4001,
                status="deal",
                buyer_name="Тест",
            ),
        )

        fake_llm = SimpleFakeLLM(responses=[response])

        edit_deal_agent = EditDealAgentServiceImpl(
            llm=fake_llm, edit_deal_prompts=edit_deal_prompts
        )

        result_state = await edit_deal_agent(state=state)

        assert result_state.result == response
