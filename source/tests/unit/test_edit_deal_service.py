"""
Тесты для EditDealAgentServiceImpl.

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


@pytest.fixture
def state_edit_amount() -> State:
    """Запрос на изменение суммы."""
    return State(
        telegram_user_id=uuid4(),
        telegram_chat_id=123456,
        crm_user_id=100,
        user_role="manager",
        user_input="Измени сумму сделки на 750000",
        deal_data=DealData(
            crm_deal_id=2001,
            status="deal",
            buyer_name="ООО Покупатель",
            seller_name="ООО Продавец",
            total_amount=500000.0,
        ),
    )


@pytest.fixture
def state_edit_buyer_name() -> State:
    """Запрос на изменение имени покупателя."""
    return State(
        telegram_user_id=uuid4(),
        telegram_chat_id=123456,
        crm_user_id=100,
        user_role="manager",
        user_input="Измени покупателя на ООО Новый Покупатель",
        deal_data=DealData(
            crm_deal_id=3001,
            status="deal",
            buyer_name="ООО Старый Покупатель",
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
        fake_llm = FakeChatModel(
            responses=[
                AIMessage(
                    content="Дата погрузки по сделке 1001 изменена на 20 января"
                )
            ]
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
        fake_llm = FakeChatModel(
            responses=[AIMessage(content="Изменение успешно применено")]
        )

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

    async def test_converts_response_to_string(
        self,
        edit_deal_prompts: EditDealAgentPrompts,
        state_edit_amount: State,
    ):
        """Агент корректно преобразует ответ в строку."""
        fake_llm = FakeChatModel(responses=[AIMessage(content="Сумма обновлена")])

        edit_deal_agent = EditDealAgentServiceImpl(
            llm=fake_llm, edit_deal_prompts=edit_deal_prompts
        )

        result_state = await edit_deal_agent(state=state_edit_amount)

        assert isinstance(result_state.result, str)
        assert result_state.result == "Сумма обновлена"


class TestEditDealAgentServiceScenarios:
    """Тесты различных сценариев редактирования."""

    async def test_edit_loading_date(
        self,
        edit_deal_prompts: EditDealAgentPrompts,
        state_edit_loading_date: State,
    ):
        """Изменение даты погрузки."""
        fake_llm = FakeChatModel(
            responses=[
                AIMessage(
                    content="Дата погрузки успешно изменена на 20 января 2026"
                )
            ]
        )

        edit_deal_agent = EditDealAgentServiceImpl(
            llm=fake_llm, edit_deal_prompts=edit_deal_prompts
        )

        result_state = await edit_deal_agent(state=state_edit_loading_date)

        assert "погрузки" in result_state.result.lower()
        assert "20 января" in result_state.result

    async def test_edit_amount(
        self,
        edit_deal_prompts: EditDealAgentPrompts,
        state_edit_amount: State,
    ):
        """Изменение суммы сделки."""
        fake_llm = FakeChatModel(
            responses=[
                AIMessage(content="Сумма сделки 2001 изменена на 750 000 руб")
            ]
        )

        edit_deal_agent = EditDealAgentServiceImpl(
            llm=fake_llm, edit_deal_prompts=edit_deal_prompts
        )

        result_state = await edit_deal_agent(state=state_edit_amount)

        assert "сумма" in result_state.result.lower()
        assert "750 000" in result_state.result

    async def test_edit_buyer_name(
        self,
        edit_deal_prompts: EditDealAgentPrompts,
        state_edit_buyer_name: State,
    ):
        """Изменение имени покупателя."""
        fake_llm = FakeChatModel(
            responses=[
                AIMessage(
                    content="Покупатель изменен на ООО Новый Покупатель по сделке 3001"
                )
            ]
        )

        edit_deal_agent = EditDealAgentServiceImpl(
            llm=fake_llm, edit_deal_prompts=edit_deal_prompts
        )

        result_state = await edit_deal_agent(state=state_edit_buyer_name)

        assert "покупатель" in result_state.result.lower()
        assert "Новый Покупатель" in result_state.result

    @pytest.mark.parametrize(
        "edit_request,expected_keyword",
        [
            ("Измени дату погрузки", "погрузк"),
            ("Измени дату разгрузки", "разгрузк"),
            ("Измени сумму", "сумм"),
            ("Измени покупателя", "покупател"),
            ("Измени продавца", "продав"),
            ("Измени комментарий", "комментар"),
        ],
    )
    async def test_different_field_edits(
        self,
        edit_deal_prompts: EditDealAgentPrompts,
        edit_request: str,
        expected_keyword: str,
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

        fake_llm = FakeChatModel(
            responses=[AIMessage(content=f"{edit_request} - выполнено")]
        )

        edit_deal_agent = EditDealAgentServiceImpl(
            llm=fake_llm, edit_deal_prompts=edit_deal_prompts
        )

        result_state = await edit_deal_agent(state=state)

        assert expected_keyword in result_state.result.lower()


class TestEditDealAgentServiceResponseHandling:
    """Тесты обработки различных форматов ответов."""

    async def test_handles_string_content(
        self,
        edit_deal_prompts: EditDealAgentPrompts,
        state_edit_loading_date: State,
    ):
        """Обработка строкового content."""
        fake_llm = FakeChatModel(
            responses=[AIMessage(content="Изменения применены")]
        )

        edit_deal_agent = EditDealAgentServiceImpl(
            llm=fake_llm, edit_deal_prompts=edit_deal_prompts
        )

        result_state = await edit_deal_agent(state=state_edit_loading_date)

        assert result_state.result == "Изменения применены"

    async def test_handles_multiline_response(
        self,
        edit_deal_prompts: EditDealAgentPrompts,
        state_edit_amount: State,
    ):
        """Обработка многострочного ответа."""
        multiline_response = """Сделка 2001 обновлена:

        Изменено:
        - Сумма: 500 000 → 750 000 руб

        Статус: успешно"""

        fake_llm = FakeChatModel(responses=[AIMessage(content=multiline_response)])

        edit_deal_agent = EditDealAgentServiceImpl(
            llm=fake_llm, edit_deal_prompts=edit_deal_prompts
        )

        result_state = await edit_deal_agent(state=state_edit_amount)

        assert result_state.result == multiline_response
        assert "750 000" in result_state.result

    async def test_handles_edit_confirmation(
        self,
        edit_deal_prompts: EditDealAgentPrompts,
    ):
        """Обработка подробного подтверждения изменений."""
        now = datetime.now(timezone.utc)
        state = State(
            telegram_user_id=uuid4(),
            telegram_chat_id=123456,
            crm_user_id=100,
            user_role="manager",
            user_input="Измени дату оплаты на 25 января",
            deal_data=DealData(
                crm_deal_id=5001,
                status="deal",
                buyer_name="ООО Покупатель",
                payment_date=now + timedelta(days=7),
            ),
        )

        detailed_response = """Дата оплаты изменена:
        - Сделка: 5001
        - Старая дата: 15 января 2026
        - Новая дата: 25 января 2026
        - Изменено: успешно"""

        fake_llm = FakeChatModel(responses=[AIMessage(content=detailed_response)])

        edit_deal_agent = EditDealAgentServiceImpl(
            llm=fake_llm, edit_deal_prompts=edit_deal_prompts
        )

        result_state = await edit_deal_agent(state=state)

        assert "5001" in result_state.result
        assert "25 января" in result_state.result

    async def test_handles_validation_error_response(
        self,
        edit_deal_prompts: EditDealAgentPrompts,
    ):
        """Обработка ответа с ошибкой валидации."""
        state = State(
            telegram_user_id=uuid4(),
            telegram_chat_id=123456,
            crm_user_id=100,
            user_role="manager",
            user_input="Измени сумму на -1000",
            deal_data=DealData(
                crm_deal_id=6001,
                status="deal",
                total_amount=500000.0,
            ),
        )

        error_response = "Ошибка: сумма сделки не может быть отрицательной"

        fake_llm = FakeChatModel(responses=[AIMessage(content=error_response)])

        edit_deal_agent = EditDealAgentServiceImpl(
            llm=fake_llm, edit_deal_prompts=edit_deal_prompts
        )

        result_state = await edit_deal_agent(state=state)

        assert "ошибка" in result_state.result.lower()
