"""
Тесты для ReminderAgentServiceImpl.

Используется подход:
- SimpleFakeLLM (свой Mock класс)
- Реальные промпты
- Фикстуры для State
"""

from uuid import uuid4
from datetime import datetime, timezone, timedelta
import pytest

from source.tests.unit.fake_llm import SimpleFakeLLM
from source.api.agents.reminder.service_impl import ReminderAgentServiceImpl
from source.schemas.pydantic.agents import State, DealData
from source.services.prompts.reminder_prompts import ReminderAgentPrompts


@pytest.fixture
def reminder_prompts() -> ReminderAgentPrompts:
    """Фикстура для создания ReminderAgentPrompts."""
    return ReminderAgentPrompts()


@pytest.fixture
def state_with_deal_dates() -> State:
    """Состояние с данными о сделке и датами."""
    now = datetime.now(timezone.utc)
    return State(
        telegram_user_id=uuid4(),
        telegram_chat_id=123456,
        crm_user_id=100,
        user_role="manager",
        user_input="Когда погрузка по сделке?",
        deal_data=DealData(
            crm_deal_id=1001,
            status="deal",
            buyer_name="ООО Покупатель",
            total_amount=500000.0,
            loading_date=now + timedelta(days=2),
            unloading_date=now + timedelta(days=4),
            payment_date=now + timedelta(days=7),
        ),
    )


class TestReminderAgentServiceBasic:
    """Базовые тесты ReminderAgentService."""

    async def test_returns_reminder_response(
        self,
        reminder_prompts: ReminderAgentPrompts,
        state_with_deal_dates: State,
    ):
        """Агент возвращает ответ о датах."""
        fake_llm = SimpleFakeLLM(
            responses=["Погрузка запланирована на 10 января 2026"]
        )

        reminder_agent = ReminderAgentServiceImpl(
            llm=fake_llm, reminder_prompts=reminder_prompts
        )

        result_state = await reminder_agent(state=state_with_deal_dates)

        assert result_state.result is not None
        assert result_state.result == "Погрузка запланирована на 10 января 2026"

    async def test_preserves_state_fields(
        self,
        reminder_prompts: ReminderAgentPrompts,
        state_with_deal_dates: State,
    ):
        """Агент сохраняет все поля состояния."""
        fake_llm = SimpleFakeLLM(responses=["Дата погрузки: через 2 дня"])

        reminder_agent = ReminderAgentServiceImpl(
            llm=fake_llm, reminder_prompts=reminder_prompts
        )

        result_state = await reminder_agent(state=state_with_deal_dates)

        # Все исходные поля сохранились
        assert result_state.telegram_user_id == state_with_deal_dates.telegram_user_id
        assert result_state.user_input == state_with_deal_dates.user_input
        assert result_state.deal_data is not None
        assert result_state.deal_data.crm_deal_id == 1001
        # И добавился result
        assert result_state.result is not None

    @pytest.mark.parametrize(
        "user_question,expected_response",
        [
            ("Когда погрузка?", "Погрузка 15 января"),
            ("Когда разгрузка?", "Разгрузка 17 января"),
            ("Когда оплата?", "Оплата ожидается 20 января"),
        ],
    )
    async def test_different_date_queries(
        self,
        reminder_prompts: ReminderAgentPrompts,
        user_question: str,
        expected_response: str,
    ):
        """Проверка разных типов вопросов о датах."""
        state = State(
            telegram_user_id=uuid4(),
            telegram_chat_id=123456,
            crm_user_id=100,
            user_role="manager",
            user_input=user_question,
        )

        fake_llm = SimpleFakeLLM(responses=[expected_response])

        reminder_agent = ReminderAgentServiceImpl(
            llm=fake_llm, reminder_prompts=reminder_prompts
        )

        result_state = await reminder_agent(state=state)

        assert result_state.result == expected_response
