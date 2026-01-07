from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from source.db.models.application import Application
from source.api.interfaces.application.gateway_abc import ApplicationGatewayAbc
from source.config.logging import logger


class ApplicationGatewayImpl(ApplicationGatewayAbc):
    """
    Реализация gateway для работы с заявками в БД.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, application_id: UUID) -> Optional[Application]:
        """Получить заявку по UUID"""
        try:
            stmt = select(Application).where(Application.id == application_id)
            result = await self._session.execute(statement=stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"[APPLICATION_GATEWAY] Error getting application by id {application_id}: {e}"
            )
            return None

    async def get_by_crm_id(self, crm_application_id: int) -> Optional[Application]:
        """Получить заявку по CRM ID"""
        try:
            stmt = select(Application).where(
                Application.crm_application_id == crm_application_id
            )
            result = await self._session.execute(statement=stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"[APPLICATION_GATEWAY] Error getting application by crm_id {crm_application_id}: {e}"
            )
            return None

    async def get_user_applications(
        self,
        crm_user_id: int,
        limit: int = 10,
    ) -> list[Application]:
        """Получить заявки пользователя"""
        try:
            stmt = (
                select(Application)
                .where(Application.owner_crm_id == crm_user_id)
                .order_by(Application.created_date.desc())
                .limit(limit)
            )
            result = await self._session.execute(statement=stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(
                f"[APPLICATION_GATEWAY] Error getting user applications for user {crm_user_id}: {e}"
            )
            return []

    async def get_by_type(
        self,
        application_type: str,
        limit: int = 10,
    ) -> list[Application]:
        """Получить заявки по типу (buyer/seller)"""
        try:
            stmt = (
                select(Application)
                .where(Application.application_type == application_type)
                .order_by(Application.created_date.desc())
                .limit(limit)
            )
            result = await self._session.execute(statement=stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(
                f"[APPLICATION_GATEWAY] Error getting applications by type {application_type}: {e}"
            )
            return []

    async def create(self, **kwargs) -> Application:
        """Создать новую заявку"""
        try:
            application = Application(**kwargs)
            self._session.add(instance=application)
            await self._session.flush()
            await self._session.refresh(instance=application)
            return application
        except Exception as e:
            logger.error(f"[APPLICATION_GATEWAY] Error creating application: {e}")
            raise

    async def update(self, application: Application, **kwargs) -> Application:
        """Обновить существующую заявку"""
        try:
            for key, value in kwargs.items():
                if hasattr(application, key):
                    setattr(application, key, value)
            await self._session.flush()
            await self._session.refresh(instance=application)
            return application
        except Exception as e:
            logger.error(
                f"[APPLICATION_GATEWAY] Error updating application {application.id}: {e}"
            )
            raise
