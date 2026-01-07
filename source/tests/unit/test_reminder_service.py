"""
Тесты для ReminderAgentServiceImpl.

Используется подход:
- FakeChatModel из langchain для тестирования LLM (не Mock!)
- Реальные промпты
- Фикстуры для State
- Parametrize для разных сценариев
"""

from uuid import uuid4
from datetime import datetime, timezone, timedelta
import pytest
from langchain_core.messages import AIMessage
from langchain_core.language_models.fake_chat_models import FakeChatModel

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


@pytest.fixture
def state_asking_about_loading() -> State:
    """Пользователь спрашивает о погрузке."""
    return State(
        telegram_user_id=uuid4(),
        telegram_chat_id=123456,
        crm_user_id=100,
        user_role="manager",
        user_input="Когда погрузка по сделке 1001?",
    )


@pytest.fixture
def state_asking_about_payment() -> State:
    """Пользователь спрашивает об оплате."""
    now = datetime.now(timezone.utc)
    return State(
        telegram_user_id=uuid4(),
        telegram_chat_id=123456,
        crm_user_id=100,
        user_role="manager",
        user_input="Когда оплата?",
        deal_data=DealData(
            crm_deal_id=2001,
            status="deal",
            payment_date=now + timedelta(days=5),
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
        fake_llm = FakeChatModel(
            responses=[AIMessage(content="Погрузка запланирована на 10 января 2026")]
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
        fake_llm = FakeChatModel(
            responses=[AIMessage(content="Дата погрузки: через 2 дня")]
        )

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

    async def test_converts_response_to_string(
        self,
        reminder_prompts: ReminderAgentPrompts,
        state_asking_about_loading: State,
    ):
        """Агент корректно преобразует ответ в строку."""
        # AIMessage с content
        fake_llm = FakeChatModel(
            responses=[AIMessage(content="Ответ о погрузке")]
        )

        reminder_agent = ReminderAgentServiceImpl(
            llm=fake_llm, reminder_prompts=reminder_prompts
        )

        result_state = await reminder_agent(state=state_asking_about_loading)

        assert isinstance(result_state.result, str)
        assert result_state.result == "Ответ о погрузке"


class TestReminderAgentServiceScenarios:
    """Тесты различных сценариев использования."""

    async def test_loading_date_query(
        self,
        reminder_prompts: ReminderAgentPrompts,
        state_asking_about_loading: State,
    ):
        """Запрос о дате погрузки."""
        fake_llm = FakeChatModel(
            responses=[
                AIMessage(
                    content="По сделке 1001 погрузка запланирована на 15 января 2026"
                )
            ]
        )

        reminder_agent = ReminderAgentServiceImpl(
            llm=fake_llm, reminder_prompts=reminder_prompts
        )

        result_state = await reminder_agent(state=state_asking_about_loading)

        assert "погрузка" in result_state.result.lower()
        assert "1001" in result_state.result

    async def test_payment_date_query(
        self,
        reminder_prompts: ReminderAgentPrompts,
        state_asking_about_payment: State,
    ):
        """Запрос о дате оплаты."""
        fake_llm = FakeChatModel(
            responses=[AIMessage(content="Оплата ожидается через 5 дней")]
        )

        reminder_agent = ReminderAgentServiceImpl(
            llm=fake_llm, reminder_prompts=reminder_prompts
        )

        result_state = await reminder_agent(state=state_asking_about_payment)

        assert result_state.result is not None
        assert "оплата" in result_state.result.lower()

    @pytest.mark.parametrize(
        "user_question,expected_keyword",
        [
            ("Когда погрузка?", "погрузка"),
            ("Когда разгрузка?", "разгрузка"),
            ("Когда оплата по сделке?", "оплата"),
            ("Какие даты по сделке?", "дат"),
        ],
    )
    async def test_different_date_queries(
        self,
        reminder_prompts: ReminderAgentPrompts,
        user_question: str,
        expected_keyword: str,
    ):
        """Проверка разных типов вопросов о датах."""
        state = State(
            telegram_user_id=uuid4(),
            telegram_chat_id=123456,
            crm_user_id=100,
            user_role="manager",
            user_input=user_question,
        )

        fake_llm = FakeChatModel(
            responses=[AIMessage(content=f"Информация о {expected_keyword}")]
        )

        reminder_agent = ReminderAgentServiceImpl(
            llm=fake_llm, reminder_prompts=reminder_prompts
        )

        result_state = await reminder_agent(state=state)

        assert result_state.result is not None
        assert expected_keyword in result_state.result.lower()


class TestReminderAgentServiceResponseHandling:
    """Тесты обработки различных форматов ответов."""

    async def test_handles_string_content(
        self,
        reminder_prompts: ReminderAgentPrompts,
        state_asking_about_loading: State,
    ):
        """Обработка строкового content."""
        fake_llm = FakeChatModel(
            responses=[AIMessage(content="Простой текстовый ответ")]
        )

        reminder_agent = ReminderAgentServiceImpl(
            llm=fake_llm, reminder_prompts=reminder_prompts
        )

        result_state = await reminder_agent(state=state_asking_about_loading)

        assert result_state.result == "Простой текстовый ответ"

    async def test_handles_multiline_response(
        self,
        reminder_prompts: ReminderAgentPrompts,
        state_with_deal_dates: State,
    ):
        """Обработка многострочного ответа."""
        multiline_response = """По сделке 1001:
        - Погрузка: 10 января
        - Разгрузка: 12 января
        - Оплата: 15 января"""

        fake_llm = FakeChatModel(responses=[AIMessage(content=multiline_response)])

        reminder_agent = ReminderAgentServiceImpl(
            llm=fake_llm, reminder_prompts=reminder_prompts
        )

        result_state = await reminder_agent(state=state_with_deal_dates)

        assert result_state.result == multiline_response
        assert "Погрузка" in result_state.result
        assert "Оплата" in result_state.result

    async def test_handles_empty_response(
        self,
        reminder_prompts: ReminderAgentPrompts,
        state_asking_about_loading: State,
    ):
        """Обработка пустого ответа."""
        fake_llm = FakeChatModel(responses=[AIMessage(content="")])

        reminder_agent = ReminderAgentServiceImpl(
            llm=fake_llm, reminder_prompts=reminder_prompts
        )

        result_state = await reminder_agent(state=state_asking_about_loading)

        assert result_state.result == ""
