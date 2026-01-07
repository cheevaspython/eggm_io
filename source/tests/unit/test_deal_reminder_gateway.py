"""
Тесты для DealReminderGatewayImpl.

Используется подход:
- Реальная БД сессия (test_db_session)
- Фикстуры для создания тестовых данных
- Parametrize для проверки разных сценариев
- НЕТ Mock объектов
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4, UUID
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from source.api.interfaces.deal_reminder.gateway_impl import DealReminderGatewayImpl
from source.db.models.deal_reminder import DealReminder


@pytest.fixture
async def reminder_gateway(test_db_session: AsyncSession) -> DealReminderGatewayImpl:
    """Фикстура для создания DealReminderGatewayImpl с тестовой сессией."""
    return DealReminderGatewayImpl(session=test_db_session)


@pytest.fixture
async def sample_reminder(test_db_session: AsyncSession) -> DealReminder:
    """Создает тестовое напоминание в БД."""
    now = datetime.now(timezone.utc)
    reminder = DealReminder(
        deal_id=uuid4(),
        crm_deal_id=1001,
        telegram_user_id=uuid4(),
        reminder_type="loading",
        remind_at=now + timedelta(hours=1),
        target_date=now + timedelta(days=1),
        is_sent=False,
        retry_count=0,
    )
    test_db_session.add(instance=reminder)
    await test_db_session.commit()
    await test_db_session.refresh(instance=reminder)
    return reminder


@pytest.fixture
async def multiple_reminders(test_db_session: AsyncSession) -> list[DealReminder]:
    """Создает несколько напоминаний для тестирования."""
    now = datetime.now(timezone.utc)
    deal_id_1 = uuid4()
    deal_id_2 = uuid4()
    user_id_1 = uuid4()
    user_id_2 = uuid4()

    reminders = [
        # Pending reminders для user_id_1
        DealReminder(
            deal_id=deal_id_1,
            crm_deal_id=2001,
            telegram_user_id=user_id_1,
            reminder_type="loading",
            remind_at=now + timedelta(hours=1),
            target_date=now + timedelta(days=1),
            is_sent=False,
        ),
        DealReminder(
            deal_id=deal_id_1,
            crm_deal_id=2001,
            telegram_user_id=user_id_1,
            reminder_type="payment",
            remind_at=now + timedelta(hours=2),
            target_date=now + timedelta(days=2),
            is_sent=False,
        ),
        # Sent reminder
        DealReminder(
            deal_id=deal_id_1,
            crm_deal_id=2001,
            telegram_user_id=user_id_1,
            reminder_type="unloading",
            remind_at=now - timedelta(hours=1),
            target_date=now,
            is_sent=True,
            sent_at=now - timedelta(minutes=30),
        ),
        # Future reminder
        DealReminder(
            deal_id=deal_id_2,
            crm_deal_id=2002,
            telegram_user_id=user_id_2,
            reminder_type="confirmation",
            remind_at=now + timedelta(days=5),
            target_date=now + timedelta(days=6),
            is_sent=False,
        ),
        # Past pending reminder (должно быть отправлено)
        DealReminder(
            deal_id=deal_id_2,
            crm_deal_id=2002,
            telegram_user_id=user_id_2,
            reminder_type="loading",
            remind_at=now - timedelta(hours=2),
            target_date=now - timedelta(hours=1),
            is_sent=False,
        ),
    ]
    for reminder in reminders:
        test_db_session.add(instance=reminder)
    await test_db_session.commit()
    for reminder in reminders:
        await test_db_session.refresh(instance=reminder)
    return reminders


class TestDealReminderGatewayCreate:
    """Тесты для создания напоминаний."""

    async def test_create_minimal_reminder(
        self,
        reminder_gateway: DealReminderGatewayImpl,
    ):
        """Создание напоминания с минимальным набором полей."""
        now = datetime.now(timezone.utc)
        reminder = await reminder_gateway.create(
            deal_id=uuid4(),
            crm_deal_id=3001,
            telegram_user_id=uuid4(),
            reminder_type="loading",
            remind_at=now + timedelta(hours=1),
            target_date=now + timedelta(days=1),
        )

        assert reminder.id is not None
        assert reminder.crm_deal_id == 3001
        assert reminder.reminder_type == "loading"
        assert reminder.is_sent is False
        assert reminder.retry_count == 0
        assert reminder.created_date is not None

    async def test_create_loading_reminder(
        self,
        reminder_gateway: DealReminderGatewayImpl,
    ):
        """Создание напоминания о погрузке."""
        now = datetime.now(timezone.utc)
        deal_id = uuid4()
        user_id = uuid4()

        reminder = await reminder_gateway.create(
            deal_id=deal_id,
            crm_deal_id=3002,
            telegram_user_id=user_id,
            reminder_type="loading",
            remind_at=now + timedelta(hours=12),
            target_date=now + timedelta(days=1),
            message_text="Напоминание о погрузке завтра",
        )

        assert reminder.reminder_type == "loading"
        assert reminder.message_text == "Напоминание о погрузке завтра"

    async def test_create_payment_reminder(
        self,
        reminder_gateway: DealReminderGatewayImpl,
    ):
        """Создание напоминания об оплате."""
        now = datetime.now(timezone.utc)
        reminder = await reminder_gateway.create(
            deal_id=uuid4(),
            crm_deal_id=3003,
            telegram_user_id=uuid4(),
            reminder_type="payment",
            remind_at=now + timedelta(days=2),
            target_date=now + timedelta(days=3),
            message_text="Ожидается оплата через 3 дня",
            additional_info="Сумма: 500000 руб",
        )

        assert reminder.reminder_type == "payment"
        assert reminder.additional_info == "Сумма: 500000 руб"

    @pytest.mark.parametrize(
        "reminder_type", ["loading", "unloading", "payment", "confirmation"]
    )
    async def test_create_with_all_types(
        self,
        reminder_gateway: DealReminderGatewayImpl,
        reminder_type: str,
    ):
        """Проверка создания напоминаний всех типов."""
        now = datetime.now(timezone.utc)
        crm_id = 4000 + hash(reminder_type) % 1000

        reminder = await reminder_gateway.create(
            deal_id=uuid4(),
            crm_deal_id=crm_id,
            telegram_user_id=uuid4(),
            reminder_type=reminder_type,
            remind_at=now + timedelta(hours=1),
            target_date=now + timedelta(days=1),
        )

        assert reminder.reminder_type == reminder_type


class TestDealReminderGatewayGet:
    """Тесты для получения напоминаний."""

    async def test_get_by_id_exists(
        self,
        reminder_gateway: DealReminderGatewayImpl,
        sample_reminder: DealReminder,
    ):
        """Получение существующего напоминания по ID."""
        reminder = await reminder_gateway.get_by_id(reminder_id=sample_reminder.id)

        assert reminder is not None
        assert reminder.id == sample_reminder.id
        assert reminder.crm_deal_id == sample_reminder.crm_deal_id

    async def test_get_by_id_not_exists(
        self,
        reminder_gateway: DealReminderGatewayImpl,
    ):
        """Получение несуществующего напоминания."""
        random_uuid = uuid4()
        reminder = await reminder_gateway.get_by_id(reminder_id=random_uuid)

        assert reminder is None

    async def test_get_pending_reminders_has_pending(
        self,
        reminder_gateway: DealReminderGatewayImpl,
        multiple_reminders: list[DealReminder],
    ):
        """Получение неотправленных напоминаний."""
        now = datetime.now(timezone.utc)
        until = now + timedelta(hours=3)

        reminders = await reminder_gateway.get_pending_reminders(until=until)

        # Должны быть: 2 pending в пределах 3 часов + 1 прошедшее
        assert len(reminders) >= 3
        for reminder in reminders:
            assert reminder.is_sent is False
            assert reminder.remind_at <= until

    async def test_get_pending_reminders_no_pending(
        self,
        reminder_gateway: DealReminderGatewayImpl,
    ):
        """Нет неотправленных напоминаний в прошлом."""
        past = datetime.now(timezone.utc) - timedelta(days=10)

        reminders = await reminder_gateway.get_pending_reminders(until=past)

        assert reminders == []

    @pytest.mark.parametrize("hours_ahead", [1, 2, 5, 24])
    async def test_get_pending_reminders_filters_by_date(
        self,
        reminder_gateway: DealReminderGatewayImpl,
        multiple_reminders: list[DealReminder],
        hours_ahead: int,
    ):
        """Проверка фильтрации по дате."""
        now = datetime.now(timezone.utc)
        until = now + timedelta(hours=hours_ahead)

        reminders = await reminder_gateway.get_pending_reminders(until=until)

        # Все напоминания должны быть до указанной даты
        for reminder in reminders:
            assert reminder.remind_at <= until
            assert reminder.is_sent is False

    async def test_get_pending_reminders_excludes_sent(
        self,
        reminder_gateway: DealReminderGatewayImpl,
        multiple_reminders: list[DealReminder],
    ):
        """Отправленные напоминания не возвращаются."""
        now = datetime.now(timezone.utc)
        until = now + timedelta(days=10)  # Большой период

        reminders = await reminder_gateway.get_pending_reminders(until=until)

        # Проверяем что ни одно из возвращенных напоминаний не отправлено
        for reminder in reminders:
            assert reminder.is_sent is False

    async def test_get_pending_reminders_sorted(
        self,
        reminder_gateway: DealReminderGatewayImpl,
        multiple_reminders: list[DealReminder],
    ):
        """Напоминания отсортированы по remind_at ASC."""
        now = datetime.now(timezone.utc)
        until = now + timedelta(days=10)

        reminders = await reminder_gateway.get_pending_reminders(until=until)

        # Проверяем сортировку
        for i in range(len(reminders) - 1):
            assert reminders[i].remind_at <= reminders[i + 1].remind_at


class TestDealReminderGatewayGetDealReminders:
    """Тесты для получения напоминаний по сделке."""

    async def test_get_deal_reminders_exists(
        self,
        reminder_gateway: DealReminderGatewayImpl,
        multiple_reminders: list[DealReminder],
    ):
        """Получение напоминаний существующей сделки."""
        # Берем deal_id из первого напоминания
        deal_id = multiple_reminders[0].deal_id

        reminders = await reminder_gateway.get_deal_reminders(deal_id=deal_id)

        # У этой сделки должно быть 3 напоминания (2 pending + 1 sent)
        assert len(reminders) == 3
        for reminder in reminders:
            assert reminder.deal_id == deal_id

    async def test_get_deal_reminders_empty(
        self,
        reminder_gateway: DealReminderGatewayImpl,
    ):
        """Получение напоминаний несуществующей сделки."""
        random_deal_id = uuid4()

        reminders = await reminder_gateway.get_deal_reminders(deal_id=random_deal_id)

        assert reminders == []

    async def test_get_deal_reminders_sorted_by_remind_at(
        self,
        reminder_gateway: DealReminderGatewayImpl,
        multiple_reminders: list[DealReminder],
    ):
        """Напоминания отсортированы по remind_at ASC."""
        deal_id = multiple_reminders[0].deal_id

        reminders = await reminder_gateway.get_deal_reminders(deal_id=deal_id)

        # Проверяем сортировку
        for i in range(len(reminders) - 1):
            assert reminders[i].remind_at <= reminders[i + 1].remind_at


class TestDealReminderGatewayGetUserReminders:
    """Тесты для получения напоминаний пользователя."""

    async def test_get_user_reminders_exists(
        self,
        reminder_gateway: DealReminderGatewayImpl,
        multiple_reminders: list[DealReminder],
    ):
        """Получение напоминаний существующего пользователя."""
        # Берем user_id из первого напоминания
        user_id = multiple_reminders[0].telegram_user_id

        reminders = await reminder_gateway.get_user_reminders(
            telegram_user_id=user_id
        )

        # У этого пользователя есть неотправленные напоминания
        assert len(reminders) >= 2
        for reminder in reminders:
            assert reminder.telegram_user_id == user_id
            assert reminder.is_sent is False

    async def test_get_user_reminders_empty(
        self,
        reminder_gateway: DealReminderGatewayImpl,
    ):
        """Получение напоминаний несуществующего пользователя."""
        random_user_id = uuid4()

        reminders = await reminder_gateway.get_user_reminders(
            telegram_user_id=random_user_id
        )

        assert reminders == []

    async def test_get_user_reminders_excludes_sent(
        self,
        reminder_gateway: DealReminderGatewayImpl,
        multiple_reminders: list[DealReminder],
    ):
        """Отправленные напоминания не возвращаются."""
        user_id = multiple_reminders[0].telegram_user_id

        reminders = await reminder_gateway.get_user_reminders(
            telegram_user_id=user_id
        )

        # Проверяем что все напоминания неотправленные
        for reminder in reminders:
            assert reminder.is_sent is False

    @pytest.mark.parametrize("limit", [1, 2, 5, 10])
    async def test_get_user_reminders_with_limit(
        self,
        reminder_gateway: DealReminderGatewayImpl,
        multiple_reminders: list[DealReminder],
        limit: int,
    ):
        """Проверка ограничения количества напоминаний."""
        user_id = multiple_reminders[0].telegram_user_id

        reminders = await reminder_gateway.get_user_reminders(
            telegram_user_id=user_id, limit=limit
        )

        assert len(reminders) <= limit

    async def test_get_user_reminders_sorted(
        self,
        reminder_gateway: DealReminderGatewayImpl,
        multiple_reminders: list[DealReminder],
    ):
        """Напоминания отсортированы по remind_at ASC."""
        user_id = multiple_reminders[0].telegram_user_id

        reminders = await reminder_gateway.get_user_reminders(
            telegram_user_id=user_id
        )

        # Проверяем сортировку
        for i in range(len(reminders) - 1):
            assert reminders[i].remind_at <= reminders[i + 1].remind_at


class TestDealReminderGatewayMarkAsSent:
    """Тесты для отметки напоминания как отправленного."""

    async def test_mark_as_sent_sets_flags(
        self,
        reminder_gateway: DealReminderGatewayImpl,
        sample_reminder: DealReminder,
    ):
        """Отметка устанавливает is_sent в True."""
        assert sample_reminder.is_sent is False
        assert sample_reminder.sent_at is None

        updated_reminder = await reminder_gateway.mark_as_sent(
            reminder=sample_reminder
        )

        assert updated_reminder.is_sent is True
        assert updated_reminder.sent_at is not None

    async def test_mark_as_sent_sets_timestamp(
        self,
        reminder_gateway: DealReminderGatewayImpl,
        sample_reminder: DealReminder,
    ):
        """Отметка устанавливает sent_at близко к текущему времени."""
        before = datetime.now(timezone.utc)
        updated_reminder = await reminder_gateway.mark_as_sent(
            reminder=sample_reminder
        )
        after = datetime.now(timezone.utc)

        assert updated_reminder.sent_at is not None
        # ВАЖНО: этот тест может упасть если в mark_as_sent используется
        # datetime.now() без timezone.utc - проверяем баг!
        assert before <= updated_reminder.sent_at <= after

    async def test_mark_as_sent_persists_in_db(
        self,
        reminder_gateway: DealReminderGatewayImpl,
        sample_reminder: DealReminder,
        test_db_session: AsyncSession,
    ):
        """Проверка что отметка сохраняется в БД."""
        reminder_id = sample_reminder.id

        await reminder_gateway.mark_as_sent(reminder=sample_reminder)

        # Очищаем сессию и загружаем заново
        test_db_session.expire_all()
        reminder_from_db = await reminder_gateway.get_by_id(reminder_id=reminder_id)

        assert reminder_from_db is not None
        assert reminder_from_db.is_sent is True
        assert reminder_from_db.sent_at is not None


class TestDealReminderGatewayIncrementRetry:
    """Тесты для увеличения счетчика попыток."""

    async def test_increment_retry_increments_count(
        self,
        reminder_gateway: DealReminderGatewayImpl,
        sample_reminder: DealReminder,
    ):
        """Счетчик увеличивается на 1."""
        initial_count = sample_reminder.retry_count
        assert initial_count == 0

        updated_reminder = await reminder_gateway.increment_retry(
            reminder=sample_reminder
        )

        assert updated_reminder.retry_count == initial_count + 1

    async def test_increment_retry_sets_timestamp(
        self,
        reminder_gateway: DealReminderGatewayImpl,
        sample_reminder: DealReminder,
    ):
        """Устанавливается last_retry_at."""
        before = datetime.now(timezone.utc)
        updated_reminder = await reminder_gateway.increment_retry(
            reminder=sample_reminder
        )
        after = datetime.now(timezone.utc)

        assert updated_reminder.last_retry_at is not None
        # ВАЖНО: этот тест может упасть если в increment_retry используется
        # datetime.now() без timezone.utc - проверяем баг!
        assert before <= updated_reminder.last_retry_at <= after

    @pytest.mark.parametrize("times", [1, 2, 3, 5])
    async def test_increment_retry_multiple_times(
        self,
        reminder_gateway: DealReminderGatewayImpl,
        sample_reminder: DealReminder,
        times: int,
    ):
        """Проверка множественных инкрементов."""
        for i in range(times):
            await reminder_gateway.increment_retry(reminder=sample_reminder)

        assert sample_reminder.retry_count == times

    async def test_increment_retry_persists_in_db(
        self,
        reminder_gateway: DealReminderGatewayImpl,
        sample_reminder: DealReminder,
        test_db_session: AsyncSession,
    ):
        """Проверка что инкремент сохраняется в БД."""
        reminder_id = sample_reminder.id

        await reminder_gateway.increment_retry(reminder=sample_reminder)
        await reminder_gateway.increment_retry(reminder=sample_reminder)

        # Очищаем сессию и загружаем заново
        test_db_session.expire_all()
        reminder_from_db = await reminder_gateway.get_by_id(reminder_id=reminder_id)

        assert reminder_from_db is not None
        assert reminder_from_db.retry_count == 2
        assert reminder_from_db.last_retry_at is not None
