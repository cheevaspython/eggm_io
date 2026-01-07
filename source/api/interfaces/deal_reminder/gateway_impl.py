from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from source.db.models.deal_reminder import DealReminder
from source.db.gateways.deal_reminder.gateway_abc import DealReminderGatewayAbc
from source.config.logging import logger


class DealReminderGatewayImpl(DealReminderGatewayAbc):
    """
    Реализация gateway для работы с напоминаниями по сделкам в БД.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, reminder_id: UUID) -> Optional[DealReminder]:
        """Получить напоминание по UUID"""
        try:
            stmt = select(DealReminder).where(DealReminder.id == reminder_id)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"[DEAL_REMINDER_GATEWAY] Error getting reminder by id {reminder_id}: {e}"
            )
            return None

    async def get_pending_reminders(self, until: datetime) -> list[DealReminder]:
        """Получить неотправленные напоминания до указанной даты"""
        try:
            stmt = (
                select(DealReminder)
                .where(DealReminder.is_sent.is_(False))
                .where(DealReminder.remind_at <= until)
                .order_by(DealReminder.remind_at.asc())
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(
                f"[DEAL_REMINDER_GATEWAY] Error getting pending reminders: {e}"
            )
            return []

    async def get_deal_reminders(self, deal_id: UUID) -> list[DealReminder]:
        """Получить все напоминания по сделке"""
        try:
            stmt = (
                select(DealReminder)
                .where(DealReminder.deal_id == deal_id)
                .order_by(DealReminder.remind_at.asc())
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(
                f"[DEAL_REMINDER_GATEWAY] Error getting deal reminders for deal {deal_id}: {e}"
            )
            return []

    async def get_user_reminders(
        self,
        telegram_user_id: UUID,
        limit: int = 10,
    ) -> list[DealReminder]:
        """Получить напоминания пользователя"""
        try:
            stmt = (
                select(DealReminder)
                .where(DealReminder.telegram_user_id == telegram_user_id)
                .where(DealReminder.is_sent.is_(False))
                .order_by(DealReminder.remind_at.asc())
                .limit(limit)
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(
                f"[DEAL_REMINDER_GATEWAY] Error getting user reminders for user {telegram_user_id}: {e}"
            )
            return []

    async def create(self, **kwargs) -> DealReminder:
        """Создать новое напоминание"""
        try:
            reminder = DealReminder(**kwargs)
            self._session.add(reminder)
            await self._session.flush()
            await self._session.refresh(reminder)
            return reminder
        except Exception as e:
            logger.error(f"[DEAL_REMINDER_GATEWAY] Error creating reminder: {e}")
            raise

    async def mark_as_sent(self, reminder: DealReminder) -> DealReminder:
        """Отметить напоминание как отправленное"""
        try:
            reminder.is_sent = True
            reminder.sent_at = datetime.now()
            await self._session.flush()
            await self._session.refresh(reminder)
            return reminder
        except Exception as e:
            logger.error(
                f"[DEAL_REMINDER_GATEWAY] Error marking reminder {reminder.id} as sent: {e}"
            )
            raise

    async def increment_retry(self, reminder: DealReminder) -> DealReminder:
        """Увеличить счетчик попыток отправки"""
        try:
            reminder.retry_count += 1
            reminder.last_retry_at = datetime.now()
            await self._session.flush()
            await self._session.refresh(reminder)
            return reminder
        except Exception as e:
            logger.error(
                f"[DEAL_REMINDER_GATEWAY] Error incrementing retry for reminder {reminder.id}: {e}"
            )
            raise
