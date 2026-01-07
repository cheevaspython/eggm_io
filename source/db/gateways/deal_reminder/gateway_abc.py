from typing import Protocol, Optional
from uuid import UUID
from datetime import datetime

from source.db.models.deal_reminder import DealReminder


class DealReminderGatewayAbc(Protocol):
    """
    Протокол для работы с напоминаниями по сделкам в БД.
    """

    async def get_by_id(self, reminder_id: UUID) -> Optional[DealReminder]:
        """Получить напоминание по UUID"""
        ...

    async def get_pending_reminders(self, until: datetime) -> list[DealReminder]:
        """Получить неотправленные напоминания до указанной даты"""
        ...

    async def get_deal_reminders(self, deal_id: UUID) -> list[DealReminder]:
        """Получить все напоминания по сделке"""
        ...

    async def get_user_reminders(
        self,
        telegram_user_id: UUID,
        limit: int = 10,
    ) -> list[DealReminder]:
        """Получить напоминания пользователя"""
        ...

    async def create(self, **kwargs) -> DealReminder:
        """Создать новое напоминание"""
        ...

    async def mark_as_sent(self, reminder: DealReminder) -> DealReminder:
        """Отметить напоминание как отправленное"""
        ...

    async def increment_retry(self, reminder: DealReminder) -> DealReminder:
        """Увеличить счетчик попыток отправки"""
        ...
