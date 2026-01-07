from typing import Protocol, Optional
from uuid import UUID

from source.db.models.deal import Deal


class DealGatewayAbc(Protocol):
    """
    Протокол для работы с сделками в БД.
    """

    async def get_by_id(self, deal_id: UUID) -> Optional[Deal]:
        """Получить сделку по UUID"""
        ...

    async def get_by_crm_id(self, crm_deal_id: int) -> Optional[Deal]:
        """Получить сделку по CRM ID"""
        ...

    async def get_user_deals(
        self,
        crm_user_id: int,
        limit: int = 10,
    ) -> list[Deal]:
        """Получить сделки пользователя"""
        ...

    async def get_deals_for_reminders(
        self,
        days_ahead: int = 7,
    ) -> list[Deal]:
        """Получить сделки с приближающимися датами для напоминаний"""
        ...

    async def create(self, **kwargs) -> Deal:
        """Создать новую сделку"""
        ...

    async def update(self, deal: Deal, **kwargs) -> Deal:
        """Обновить существующую сделку"""
        ...
