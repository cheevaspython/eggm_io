from typing import Protocol, Optional
from uuid import UUID

from source.db.models.application import Application


class ApplicationGatewayAbc(Protocol):
    """
    Протокол для работы с заявками в БД.
    """

    async def get_by_id(self, application_id: UUID) -> Optional[Application]:
        """Получить заявку по UUID"""
        ...

    async def get_by_crm_id(self, crm_application_id: int) -> Optional[Application]:
        """Получить заявку по CRM ID"""
        ...

    async def get_user_applications(
        self,
        crm_user_id: int,
        limit: int = 10,
    ) -> list[Application]:
        """Получить заявки пользователя"""
        ...

    async def get_by_type(
        self,
        application_type: str,
        limit: int = 10,
    ) -> list[Application]:
        """Получить заявки по типу (buyer/seller)"""
        ...

    async def create(self, **kwargs) -> Application:
        """Создать новую заявку"""
        ...

    async def update(self, application: Application, **kwargs) -> Application:
        """Обновить существующую заявку"""
        ...
