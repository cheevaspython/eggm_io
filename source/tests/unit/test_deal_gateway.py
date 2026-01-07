"""
Тесты для DealGatewayImpl.

Проверяем CRUD операции, фильтрацию, сортировку, лимиты.
Используем реальную тестовую БД без Mock.
"""

from datetime import datetime, timedelta
from uuid import uuid4, UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from source.api.interfaces.deal.gateway_impl import DealGatewayImpl
from source.db.models.deal import Deal
from source.db.models.choises.deal_status import DealStatus


@pytest.fixture
async def deal_gateway(test_db_session: AsyncSession) -> DealGatewayImpl:
    """Фикстура для создания DealGatewayImpl с тестовой сессией."""
    return DealGatewayImpl(session=test_db_session)


@pytest.fixture
async def sample_deal(test_db_session: AsyncSession) -> Deal:
    """Создает тестовую сделку в БД."""
    deal = Deal(
        crm_deal_id=1001,
        status=DealStatus.calculation,
        owner_crm_id=100,
        buyer_name="ООО Покупатель",
        seller_name="ООО Продавец",
        total_amount=50000.0,
        paid_amount=0.0,
        is_confirmed_by_manager=False,
        is_confirmed_by_director=False,
    )
    test_db_session.add(instance=deal)
    await test_db_session.commit()
    await test_db_session.refresh(instance=deal)
    return deal


@pytest.fixture
async def multiple_deals(test_db_session: AsyncSession) -> list[Deal]:
    """Создает несколько сделок для тестирования фильтрации и сортировки."""
    now = datetime.now()
    deals = [
        Deal(
            crm_deal_id=2001,
            status=DealStatus.calculation,
            owner_crm_id=200,
            buyer_name="Покупатель 1",
            total_amount=10000.0,
            loading_date=now + timedelta(days=1),
            payment_date=now + timedelta(days=5),
        ),
        Deal(
            crm_deal_id=2002,
            status=DealStatus.deal,
            owner_crm_id=200,
            buyer_name="Покупатель 2",
            total_amount=20000.0,
            loading_date=now + timedelta(days=3),
            unloading_date=now + timedelta(days=4),
        ),
        Deal(
            crm_deal_id=2003,
            status=DealStatus.closed_deal,
            owner_crm_id=201,
            buyer_name="Покупатель 3",
            total_amount=30000.0,
            loading_date=now + timedelta(days=10),  # За пределами 7 дней
        ),
        Deal(
            crm_deal_id=2004,
            status=DealStatus.calculation,
            owner_crm_id=200,
            buyer_name="Покупатель 4",
            total_amount=15000.0,
            delivery_date_from=now + timedelta(days=2),
        ),
    ]

    for deal in deals:
        test_db_session.add(instance=deal)
    await test_db_session.commit()

    for deal in deals:
        await test_db_session.refresh(instance=deal)

    return deals


class TestDealGatewayCreate:
    """Тесты создания сделок."""

    async def test_create_minimal_deal(
        self,
        deal_gateway: DealGatewayImpl,
        test_db_session: AsyncSession,
    ):
        """Создание сделки с минимальным набором обязательных полей."""
        deal = await deal_gateway.create(
            crm_deal_id=3001,
            status=DealStatus.calculation,
            owner_crm_id=300,
        )

        assert deal.id is not None
        assert deal.crm_deal_id == 3001
        assert deal.status == DealStatus.calculation
        assert deal.owner_crm_id == 300
        assert deal.created_date is not None

    async def test_create_full_deal(
        self,
        deal_gateway: DealGatewayImpl,
    ):
        """Создание сделки со всеми полями."""
        now = datetime.now()
        deal = await deal_gateway.create(
            crm_deal_id=3002,
            status=DealStatus.deal,
            owner_crm_id=301,
            manager_crm_id=401,
            buyer_name="ООО Тест Покупатель",
            seller_name="ООО Тест Продавец",
            total_amount=100000.0,
            paid_amount=50000.0,
            loading_date=now + timedelta(days=1),
            unloading_date=now + timedelta(days=3),
            payment_date=now + timedelta(days=7),
            comment="Тестовая сделка",
            is_confirmed_by_manager=True,
        )

        assert deal.id is not None
        assert deal.crm_deal_id == 3002
        assert deal.buyer_name == "ООО Тест Покупатель"
        assert deal.total_amount == 100000.0
        assert deal.paid_amount == 50000.0
        assert deal.is_confirmed_by_manager is True
        assert deal.is_confirmed_by_director is False

    @pytest.mark.parametrize("status", list(DealStatus))
    async def test_create_with_all_statuses(
        self,
        deal_gateway: DealGatewayImpl,
        status: DealStatus,
    ):
        """Проверка создания сделок со всеми возможными статусами."""
        crm_id = 4000 + status.value.__hash__() % 1000
        deal = await deal_gateway.create(
            crm_deal_id=crm_id,
            status=status,
            owner_crm_id=400,
        )

        assert deal.status == status


class TestDealGatewayGet:
    """Тесты получения сделок."""

    async def test_get_by_id_exists(
        self,
        deal_gateway: DealGatewayImpl,
        sample_deal: Deal,
    ):
        """Получение существующей сделки по UUID."""
        deal = await deal_gateway.get_by_id(deal_id=sample_deal.id)

        assert deal is not None
        assert deal.id == sample_deal.id
        assert deal.crm_deal_id == sample_deal.crm_deal_id

    async def test_get_by_id_not_exists(
        self,
        deal_gateway: DealGatewayImpl,
    ):
        """Получение несуществующей сделки должно вернуть None."""
        random_uuid = uuid4()
        deal = await deal_gateway.get_by_id(deal_id=random_uuid)

        assert deal is None

    async def test_get_by_crm_id_exists(
        self,
        deal_gateway: DealGatewayImpl,
        sample_deal: Deal,
    ):
        """Получение сделки по CRM ID."""
        deal = await deal_gateway.get_by_crm_id(crm_deal_id=sample_deal.crm_deal_id)

        assert deal is not None
        assert deal.crm_deal_id == sample_deal.crm_deal_id
        assert deal.id == sample_deal.id

    async def test_get_by_crm_id_not_exists(
        self,
        deal_gateway: DealGatewayImpl,
    ):
        """Получение несуществующей сделки по CRM ID должно вернуть None."""
        deal = await deal_gateway.get_by_crm_id(crm_deal_id=99999)

        assert deal is None


class TestDealGatewayGetUserDeals:
    """Тесты получения сделок пользователя."""

    async def test_get_user_deals_exists(
        self,
        deal_gateway: DealGatewayImpl,
        multiple_deals: list[Deal],
    ):
        """Получение сделок пользователя с owner_crm_id=200."""
        deals = await deal_gateway.get_user_deals(crm_user_id=200)

        assert len(deals) == 3  # 3 сделки с owner_crm_id=200
        # Проверяем сортировку по created_date.desc()
        for i in range(len(deals) - 1):
            assert deals[i].created_date >= deals[i + 1].created_date

    async def test_get_user_deals_empty(
        self,
        deal_gateway: DealGatewayImpl,
        multiple_deals: list[Deal],
    ):
        """Получение сделок несуществующего пользователя."""
        deals = await deal_gateway.get_user_deals(crm_user_id=999)

        assert len(deals) == 0

    @pytest.mark.parametrize("limit", [1, 2, 5, 10])
    async def test_get_user_deals_with_limit(
        self,
        deal_gateway: DealGatewayImpl,
        multiple_deals: list[Deal],
        limit: int,
    ):
        """Проверка работы параметра limit."""
        deals = await deal_gateway.get_user_deals(crm_user_id=200, limit=limit)

        expected_count = min(limit, 3)  # У нас 3 сделки с owner_crm_id=200
        assert len(deals) == expected_count


class TestDealGatewayGetDealsForReminders:
    """Тесты получения сделок для напоминаний."""

    async def test_get_deals_for_reminders_default_7_days(
        self,
        deal_gateway: DealGatewayImpl,
        multiple_deals: list[Deal],
    ):
        """Получение сделок с датами в ближайшие 7 дней."""
        deals = await deal_gateway.get_deals_for_reminders(days_ahead=7)

        # Должны найти сделки с датами от now до now+7 дней
        # crm_deal_id=2001: loading_date=now+1, payment_date=now+5 ✓
        # crm_deal_id=2002: loading_date=now+3, unloading_date=now+4 ✓
        # crm_deal_id=2003: loading_date=now+10 ✗ (за пределами 7 дней)
        # crm_deal_id=2004: delivery_date_from=now+2 ✓

        assert len(deals) >= 3  # Минимум 3 сделки должны попасть
        crm_ids = [d.crm_deal_id for d in deals]
        assert 2001 in crm_ids
        assert 2002 in crm_ids
        assert 2004 in crm_ids
        assert 2003 not in crm_ids  # Эта сделка за пределами 7 дней

    @pytest.mark.parametrize("days_ahead", [1, 3, 5, 10])
    async def test_get_deals_for_reminders_different_periods(
        self,
        deal_gateway: DealGatewayImpl,
        multiple_deals: list[Deal],
        days_ahead: int,
    ):
        """Проверка фильтрации по разным периодам."""
        deals = await deal_gateway.get_deals_for_reminders(days_ahead=days_ahead)

        # Проверяем что все даты в пределах указанного периода
        now = datetime.now()
        future_date = now + timedelta(days=days_ahead)

        for deal in deals:
            has_date_in_range = False
            dates_to_check = [
                deal.delivery_date_from,
                deal.loading_date,
                deal.unloading_date,
                deal.payment_date,
            ]

            for date in dates_to_check:
                if date and now <= date <= future_date:
                    has_date_in_range = True
                    break

            assert has_date_in_range, f"Deal {deal.crm_deal_id} не имеет дат в диапазоне"

    async def test_get_deals_for_reminders_no_dates(
        self,
        deal_gateway: DealGatewayImpl,
        test_db_session: AsyncSession,
    ):
        """Сделка без дат не должна попасть в напоминания."""
        deal = Deal(
            crm_deal_id=5001,
            status=DealStatus.calculation,
            owner_crm_id=500,
            # Без дат
        )
        test_db_session.add(instance=deal)
        await test_db_session.commit()

        deals = await deal_gateway.get_deals_for_reminders(days_ahead=7)

        crm_ids = [d.crm_deal_id for d in deals]
        assert 5001 not in crm_ids


class TestDealGatewayUpdate:
    """Тесты обновления сделок."""

    async def test_update_single_field(
        self,
        deal_gateway: DealGatewayImpl,
        sample_deal: Deal,
    ):
        """Обновление одного поля."""
        updated_deal = await deal_gateway.update(
            deal=sample_deal,
            buyer_name="ООО Новый Покупатель",
        )

        assert updated_deal.buyer_name == "ООО Новый Покупатель"
        assert updated_deal.seller_name == sample_deal.seller_name  # Не изменилось

    async def test_update_multiple_fields(
        self,
        deal_gateway: DealGatewayImpl,
        sample_deal: Deal,
    ):
        """Обновление нескольких полей."""
        updated_deal = await deal_gateway.update(
            deal=sample_deal,
            status=DealStatus.deal,
            total_amount=75000.0,
            paid_amount=25000.0,
            is_confirmed_by_manager=True,
        )

        assert updated_deal.status == DealStatus.deal
        assert updated_deal.total_amount == 75000.0
        assert updated_deal.paid_amount == 25000.0
        assert updated_deal.is_confirmed_by_manager is True

    @pytest.mark.parametrize(
        "field_name,new_value",
        [
            ("buyer_name", "Новое имя"),
            ("total_amount", 99999.99),
            ("is_confirmed_by_manager", True),
            ("is_confirmed_by_director", True),
            ("comment", "Новый комментарий"),
        ],
    )
    async def test_update_different_fields(
        self,
        deal_gateway: DealGatewayImpl,
        sample_deal: Deal,
        field_name: str,
        new_value,
    ):
        """Проверка обновления различных полей через parametrize."""
        updated_deal = await deal_gateway.update(
            deal=sample_deal,
            **{field_name: new_value},
        )

        assert getattr(updated_deal, field_name) == new_value

    async def test_update_dates(
        self,
        deal_gateway: DealGatewayImpl,
        sample_deal: Deal,
    ):
        """Обновление дат для напоминаний."""
        now = datetime.now()
        new_loading = now + timedelta(days=5)
        new_payment = now + timedelta(days=10)

        updated_deal = await deal_gateway.update(
            deal=sample_deal,
            loading_date=new_loading,
            payment_date=new_payment,
        )

        assert updated_deal.loading_date == new_loading
        assert updated_deal.payment_date == new_payment

    async def test_update_persists_in_db(
        self,
        deal_gateway: DealGatewayImpl,
        sample_deal: Deal,
        test_db_session: AsyncSession,
    ):
        """Проверка что обновления сохраняются в БД."""
        await deal_gateway.update(
            deal=sample_deal,
            buyer_name="Проверка персистентности",
        )

        # Очищаем сессию и загружаем заново из БД
        await test_db_session.expire_all()
        deal_from_db = await deal_gateway.get_by_id(deal_id=sample_deal.id)

        assert deal_from_db is not None
        assert deal_from_db.buyer_name == "Проверка персистентности"
