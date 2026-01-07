from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from source.config.logging import logger
from source.db.models.telegram_user import TelegramUser


class AuthMiddleware(BaseMiddleware):
    """
    Middleware для проверки авторизации пользователя.
    Проверяет есть ли пользователь в БД и не заблокирован ли он.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Получаем session из контекста Dishka
        session = data.get("session")

        if not isinstance(session, AsyncSession):
            logger.error("[AUTH_MIDDLEWARE] Session not found in context")
            return await handler(event, data)

        if isinstance(event, Message):
            if not event.from_user:
                logger.warning("[AUTH_MIDDLEWARE] Message from_user is None")
                return

            telegram_id = event.from_user.id

            logger.info(
                f"[AUTH_MIDDLEWARE] Checking user telegram_id={telegram_id}"
            )

            # Проверяем пользователя в БД
            try:
                stmt = select(TelegramUser).where(
                    TelegramUser.telegram_id == telegram_id
                )
                result = await session.execute(stmt)
                telegram_user = result.scalar_one_or_none()

                if not telegram_user:
                    logger.warning(
                        f"[AUTH_MIDDLEWARE] User not found: telegram_id={telegram_id}"
                    )
                    await event.answer(
                        "❌ У вас нет доступа к боту.\n"
                        "Обратитесь к администратору для получения доступа."
                    )
                    return

                if telegram_user.is_blocked:
                    logger.warning(
                        f"[AUTH_MIDDLEWARE] User blocked: telegram_id={telegram_id}"
                    )
                    await event.answer(
                        "❌ Ваш доступ к боту заблокирован.\n"
                        "Обратитесь к администратору."
                    )
                    return

                if not telegram_user.is_active:
                    logger.warning(
                        f"[AUTH_MIDDLEWARE] User inactive: telegram_id={telegram_id}"
                    )
                    await event.answer(
                        "❌ Ваш аккаунт неактивен.\n"
                        "Обратитесь к администратору."
                    )
                    return

                # Добавляем пользователя в контекст
                data["telegram_user"] = telegram_user
                logger.info(
                    f"[AUTH_MIDDLEWARE] User authorized: "
                    f"telegram_id={telegram_id}, crm_id={telegram_user.crm_user_id}, "
                    f"role={telegram_user.role.value}"
                )
            except Exception as e:
                logger.error(f"[AUTH_MIDDLEWARE] Database error: {e}", exc_info=True)
                await event.answer("❌ Ошибка проверки доступа. Попробуйте позже.")
                return

        return await handler(event, data)
