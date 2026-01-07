from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from source.db.models.deal import Deal
from source.db.gateways.deal.gateway_abc import DealGatewayAbc
from source.config.logging import logger


class DealGatewayImpl(DealGatewayAbc):
    """
    Реализация gateway для работы с сделками в БД.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, deal_id: UUID) -> Optional[Deal]:
        """Получить сделку по UUID"""
        try:
            stmt = select(Deal).where(Deal.id == deal_id)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"[DEAL_GATEWAY] Error getting deal by id {deal_id}: {e}")
            return None

    async def get_by_crm_id(self, crm_deal_id: int) -> Optional[Deal]:
        """Получить сделку по CRM ID"""
        try:
            stmt = select(Deal).where(Deal.crm_deal_id == crm_deal_id)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"[DEAL_GATEWAY] Error getting deal by crm_id {crm_deal_id}: {e}"
            )
            return None

    async def get_user_deals(
        self,
        crm_user_id: int,
        limit: int = 10,
    ) -> list[Deal]:
        """Получить сделки пользователя"""
        try:
            stmt = (
                select(Deal)
                .where(Deal.owner_crm_id == crm_user_id)
                .order_by(Deal.created_at.desc())
                .limit(limit)
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(
                f"[DEAL_GATEWAY] Error getting user deals for user {crm_user_id}: {e}"
            )
            return []

    async def get_deals_for_reminders(
        self,
        days_ahead: int = 7,
    ) -> list[Deal]:
        """Получить сделки с приближающимися датами для напоминаний"""
        try:
            now = datetime.now()
            future_date = now + timedelta(days=days_ahead)

            stmt = select(Deal).where(
                (Deal.delivery_date_from.between(now, future_date))
                | (Deal.loading_date.between(now, future_date))
                | (Deal.unloading_date.between(now, future_date))
                | (Deal.payment_date.between(now, future_date))
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"[DEAL_GATEWAY] Error getting deals for reminders: {e}")
            return []

    async def create(self, **kwargs) -> Deal:
        """Создать новую сделку"""
        try:
            deal = Deal(**kwargs)
            self._session.add(deal)
            await self._session.flush()
            await self._session.refresh(deal)
            return deal
        except Exception as e:
            logger.error(f"[DEAL_GATEWAY] Error creating deal: {e}")
            raise

    async def update(self, deal: Deal, **kwargs) -> Deal:
        """Обновить существующую сделку"""
        try:
            for key, value in kwargs.items():
                if hasattr(deal, key):
                    setattr(deal, key, value)
            await self._session.flush()
            await self._session.refresh(deal)
            return deal
        except Exception as e:
            logger.error(f"[DEAL_GATEWAY] Error updating deal {deal.id}: {e}")
            raise
