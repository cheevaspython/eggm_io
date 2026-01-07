"""
Тесты для ApplicationGatewayImpl.

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

from source.api.interfaces.application.gateway_impl import ApplicationGatewayImpl
from source.db.models.application import Application
from source.db.models.choises.deal_status import ApplicationStatus


@pytest.fixture
async def application_gateway(test_db_session: AsyncSession) -> ApplicationGatewayImpl:
    """Фикстура для создания ApplicationGatewayImpl с тестовой сессией."""
    return ApplicationGatewayImpl(session=test_db_session)


@pytest.fixture
async def sample_buyer_application(test_db_session: AsyncSession) -> Application:
    """Создает тестовую заявку от покупателя в БД."""
    application = Application(
        crm_application_id=1001,
        application_type="buyer",
        status=ApplicationStatus.active,
        owner_crm_id=100,
        client_name="ООО Покупатель",
        total_eggs_count=10000,
        price_per_egg=5.5,
        is_confirmed=False,
    )
    test_db_session.add(instance=application)
    await test_db_session.commit()
    await test_db_session.refresh(instance=application)
    return application


@pytest.fixture
async def sample_seller_application(test_db_session: AsyncSession) -> Application:
    """Создает тестовую заявку от продавца в БД."""
    application = Application(
        crm_application_id=1002,
        application_type="seller",
        status=ApplicationStatus.active,
        owner_crm_id=101,
        client_name="ООО Продавец",
        total_eggs_count=20000,
        price_per_egg=4.8,
        is_confirmed=False,
    )
    test_db_session.add(instance=application)
    await test_db_session.commit()
    await test_db_session.refresh(instance=application)
    return application


@pytest.fixture
async def multiple_applications(test_db_session: AsyncSession) -> list[Application]:
    """Создает несколько заявок для тестирования фильтрации и сортировки."""
    now = datetime.now(timezone.utc)
    applications = [
        Application(
            crm_application_id=2001,
            application_type="buyer",
            status=ApplicationStatus.active,
            owner_crm_id=200,
            client_name="Покупатель 1",
            total_eggs_count=5000,
            delivery_date_from=now + timedelta(days=1),
            delivery_date_to=now + timedelta(days=5),
        ),
        Application(
            crm_application_id=2002,
            application_type="buyer",
            status=ApplicationStatus.active,
            owner_crm_id=200,
            client_name="Покупатель 2",
            total_eggs_count=8000,
            delivery_date_from=now + timedelta(days=3),
        ),
        Application(
            crm_application_id=2003,
            application_type="seller",
            status=ApplicationStatus.active,
            owner_crm_id=200,
            client_name="Продавец 1",
            total_eggs_count=15000,
        ),
        Application(
            crm_application_id=2004,
            application_type="seller",
            status=ApplicationStatus.archived,
            owner_crm_id=201,
            client_name="Продавец 2",
            total_eggs_count=12000,
        ),
        Application(
            crm_application_id=2005,
            application_type="buyer",
            status=ApplicationStatus.in_deal,
            owner_crm_id=200,
            client_name="Покупатель 3",
            deal_crm_id=5001,
        ),
    ]
    for app in applications:
        test_db_session.add(instance=app)
    await test_db_session.commit()
    for app in applications:
        await test_db_session.refresh(instance=app)
    return applications


class TestApplicationGatewayCreate:
    """Тесты для создания заявок."""

    async def test_create_minimal_application(
        self,
        application_gateway: ApplicationGatewayImpl,
        test_db_session: AsyncSession,
    ):
        """Создание заявки с минимальным набором обязательных полей."""
        application = await application_gateway.create(
            crm_application_id=3001,
            application_type="buyer",
            status=ApplicationStatus.active,
            owner_crm_id=300,
        )

        assert application.id is not None
        assert application.crm_application_id == 3001
        assert application.application_type == "buyer"
        assert application.status == ApplicationStatus.active
        assert application.owner_crm_id == 300
        assert application.created_date is not None
        assert application.is_confirmed is False  # default

    async def test_create_buyer_application(
        self,
        application_gateway: ApplicationGatewayImpl,
    ):
        """Создание заявки от покупателя с полными данными."""
        now = datetime.now(timezone.utc)
        application = await application_gateway.create(
            crm_application_id=3002,
            application_type="buyer",
            status=ApplicationStatus.active,
            owner_crm_id=301,
            client_name="ООО Тестовый Покупатель",
            total_eggs_count=15000,
            price_per_egg=6.0,
            delivery_date_from=now + timedelta(days=7),
            delivery_date_to=now + timedelta(days=10),
            address="Москва, Ленинский проспект, 1",
            comment="Срочная заявка",
        )

        assert application.application_type == "buyer"
        assert application.client_name == "ООО Тестовый Покупатель"
        assert application.total_eggs_count == 15000
        assert application.price_per_egg == 6.0
        assert application.comment == "Срочная заявка"

    async def test_create_seller_application(
        self,
        application_gateway: ApplicationGatewayImpl,
    ):
        """Создание заявки от продавца."""
        application = await application_gateway.create(
            crm_application_id=3003,
            application_type="seller",
            status=ApplicationStatus.active,
            owner_crm_id=302,
            client_name="ИП Поставщик",
            total_eggs_count=25000,
            price_per_egg=4.5,
        )

        assert application.application_type == "seller"
        assert application.client_name == "ИП Поставщик"

    @pytest.mark.parametrize("status", list(ApplicationStatus))
    async def test_create_with_all_statuses(
        self,
        application_gateway: ApplicationGatewayImpl,
        status: ApplicationStatus,
    ):
        """Проверка создания заявок со всеми возможными статусами."""
        crm_id = 4000 + hash(status.value) % 1000
        application = await application_gateway.create(
            crm_application_id=crm_id,
            application_type="buyer",
            status=status,
            owner_crm_id=400,
        )

        assert application.status == status

    @pytest.mark.parametrize("app_type", ["buyer", "seller"])
    async def test_create_with_both_types(
        self,
        application_gateway: ApplicationGatewayImpl,
        app_type: str,
    ):
        """Проверка создания заявок обоих типов."""
        crm_id = 5000 if app_type == "buyer" else 5001
        application = await application_gateway.create(
            crm_application_id=crm_id,
            application_type=app_type,
            status=ApplicationStatus.active,
            owner_crm_id=500,
        )

        assert application.application_type == app_type


class TestApplicationGatewayGet:
    """Тесты для получения заявок."""

    async def test_get_by_id_exists(
        self,
        application_gateway: ApplicationGatewayImpl,
        sample_buyer_application: Application,
    ):
        """Получение существующей заявки по UUID."""
        application = await application_gateway.get_by_id(
            application_id=sample_buyer_application.id
        )

        assert application is not None
        assert application.id == sample_buyer_application.id
        assert application.crm_application_id == sample_buyer_application.crm_application_id

    async def test_get_by_id_not_exists(
        self,
        application_gateway: ApplicationGatewayImpl,
    ):
        """Получение несуществующей заявки по UUID."""
        random_uuid = uuid4()
        application = await application_gateway.get_by_id(application_id=random_uuid)

        assert application is None

    async def test_get_by_crm_id_exists(
        self,
        application_gateway: ApplicationGatewayImpl,
        sample_buyer_application: Application,
    ):
        """Получение существующей заявки по CRM ID."""
        application = await application_gateway.get_by_crm_id(
            crm_application_id=sample_buyer_application.crm_application_id
        )

        assert application is not None
        assert application.crm_application_id == sample_buyer_application.crm_application_id

    async def test_get_by_crm_id_not_exists(
        self,
        application_gateway: ApplicationGatewayImpl,
    ):
        """Получение несуществующей заявки по CRM ID."""
        application = await application_gateway.get_by_crm_id(
            crm_application_id=999999
        )

        assert application is None


class TestApplicationGatewayGetUserApplications:
    """Тесты для получения заявок пользователя."""

    async def test_get_user_applications_exists(
        self,
        application_gateway: ApplicationGatewayImpl,
        multiple_applications: list[Application],
    ):
        """Получение заявок существующего пользователя."""
        applications = await application_gateway.get_user_applications(
            crm_user_id=200
        )

        assert len(applications) == 4  # У пользователя 200 должно быть 4 заявки
        # Проверяем сортировку по created_date.desc()
        for i in range(len(applications) - 1):
            assert applications[i].created_date >= applications[i + 1].created_date

    async def test_get_user_applications_empty(
        self,
        application_gateway: ApplicationGatewayImpl,
    ):
        """Получение заявок несуществующего пользователя."""
        applications = await application_gateway.get_user_applications(
            crm_user_id=999999
        )

        assert applications == []

    @pytest.mark.parametrize("limit", [1, 2, 5, 10])
    async def test_get_user_applications_with_limit(
        self,
        application_gateway: ApplicationGatewayImpl,
        multiple_applications: list[Application],
        limit: int,
    ):
        """Проверка ограничения количества заявок."""
        applications = await application_gateway.get_user_applications(
            crm_user_id=200, limit=limit
        )

        expected_count = min(limit, 4)  # У пользователя 200 всего 4 заявки
        assert len(applications) == expected_count


class TestApplicationGatewayGetByType:
    """Тесты для получения заявок по типу."""

    async def test_get_by_type_buyer(
        self,
        application_gateway: ApplicationGatewayImpl,
        multiple_applications: list[Application],
    ):
        """Получение заявок от покупателей."""
        applications = await application_gateway.get_by_type(
            application_type="buyer", limit=10
        )

        assert len(applications) >= 3  # Минимум 3 buyer заявки в fixtures
        for app in applications:
            assert app.application_type == "buyer"
        # Проверяем сортировку
        for i in range(len(applications) - 1):
            assert applications[i].created_date >= applications[i + 1].created_date

    async def test_get_by_type_seller(
        self,
        application_gateway: ApplicationGatewayImpl,
        multiple_applications: list[Application],
    ):
        """Получение заявок от продавцов."""
        applications = await application_gateway.get_by_type(
            application_type="seller", limit=10
        )

        assert len(applications) >= 2  # Минимум 2 seller заявки в fixtures
        for app in applications:
            assert app.application_type == "seller"

    async def test_get_by_type_empty(
        self,
        application_gateway: ApplicationGatewayImpl,
    ):
        """Получение заявок несуществующего типа."""
        applications = await application_gateway.get_by_type(
            application_type="unknown_type", limit=10
        )

        assert applications == []

    @pytest.mark.parametrize("limit", [1, 2, 5])
    async def test_get_by_type_with_limit(
        self,
        application_gateway: ApplicationGatewayImpl,
        multiple_applications: list[Application],
        limit: int,
    ):
        """Проверка ограничения количества заявок по типу."""
        applications = await application_gateway.get_by_type(
            application_type="buyer", limit=limit
        )

        assert len(applications) <= limit


class TestApplicationGatewayUpdate:
    """Тесты для обновления заявок."""

    async def test_update_single_field(
        self,
        application_gateway: ApplicationGatewayImpl,
        sample_buyer_application: Application,
    ):
        """Обновление одного поля."""
        updated_application = await application_gateway.update(
            application=sample_buyer_application,
            client_name="ООО Новый Покупатель",
        )

        assert updated_application.client_name == "ООО Новый Покупатель"
        # Проверяем что остальные поля не изменились
        assert (
            updated_application.crm_application_id
            == sample_buyer_application.crm_application_id
        )
        assert updated_application.application_type == sample_buyer_application.application_type

    async def test_update_multiple_fields(
        self,
        application_gateway: ApplicationGatewayImpl,
        sample_buyer_application: Application,
    ):
        """Обновление нескольких полей."""
        updated_application = await application_gateway.update(
            application=sample_buyer_application,
            client_name="ООО Обновленный Покупатель",
            total_eggs_count=99999,
            price_per_egg=7.5,
            is_confirmed=True,
        )

        assert updated_application.client_name == "ООО Обновленный Покупатель"
        assert updated_application.total_eggs_count == 99999
        assert updated_application.price_per_egg == 7.5
        assert updated_application.is_confirmed is True

    @pytest.mark.parametrize(
        "field_name,new_value",
        [
            ("client_name", "Новое имя клиента"),
            ("total_eggs_count", 50000),
            ("price_per_egg", 10.0),
            ("is_confirmed", True),
            ("comment", "Обновленный комментарий"),
            ("address", "Новый адрес"),
        ],
    )
    async def test_update_different_fields(
        self,
        application_gateway: ApplicationGatewayImpl,
        sample_buyer_application: Application,
        field_name: str,
        new_value,
    ):
        """Проверка обновления разных полей."""
        updated_application = await application_gateway.update(
            application=sample_buyer_application,
            **{field_name: new_value},
        )

        assert getattr(updated_application, field_name) == new_value

    async def test_update_dates(
        self,
        application_gateway: ApplicationGatewayImpl,
        sample_buyer_application: Application,
    ):
        """Обновление дат."""
        now = datetime.now(timezone.utc)
        new_delivery_from = now + timedelta(days=5)
        new_delivery_to = now + timedelta(days=10)
        new_confirmed_at = now

        updated_application = await application_gateway.update(
            application=sample_buyer_application,
            delivery_date_from=new_delivery_from,
            delivery_date_to=new_delivery_to,
            confirmed_at=new_confirmed_at,
            is_confirmed=True,
        )

        assert updated_application.delivery_date_from == new_delivery_from
        assert updated_application.delivery_date_to == new_delivery_to
        assert updated_application.confirmed_at == new_confirmed_at
        assert updated_application.is_confirmed is True

    async def test_update_status_transition(
        self,
        application_gateway: ApplicationGatewayImpl,
        sample_buyer_application: Application,
    ):
        """Проверка перехода статуса active -> in_deal."""
        assert sample_buyer_application.status == ApplicationStatus.active

        updated_application = await application_gateway.update(
            application=sample_buyer_application,
            status=ApplicationStatus.in_deal,
            deal_crm_id=7001,
        )

        assert updated_application.status == ApplicationStatus.in_deal
        assert updated_application.deal_crm_id == 7001

    async def test_update_persists_in_db(
        self,
        application_gateway: ApplicationGatewayImpl,
        sample_buyer_application: Application,
        test_db_session: AsyncSession,
    ):
        """Проверка что обновления сохраняются в БД."""
        application_id = sample_buyer_application.id  # Сохраняем ID до expire_all()

        await application_gateway.update(
            application=sample_buyer_application,
            client_name="Проверка персистентности",
        )

        # Очищаем сессию и загружаем заново из БД
        test_db_session.expire_all()
        application_from_db = await application_gateway.get_by_id(
            application_id=application_id
        )

        assert application_from_db is not None
        assert application_from_db.client_name == "Проверка персистентности"
