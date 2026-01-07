from aiohttp import web
from aiogram import Bot
from aiogram.types import Update
from dishka.integrations.fastapi import FromDishka
from fastapi import APIRouter, Request

from source.config.logging import logger
from source.infra.telegram.bot_setup import setup_dispatcher

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    bot: FromDishka[Bot],
) -> dict:
    """
    Webhook endpoint для получения обновлений от Telegram.
    Telegram будет отправлять сюда все события (сообщения, callback и т.д.)
    """
    try:
        # Получаем dispatcher (настроенный в lifespan)
        dp = setup_dispatcher()

        # Парсим update из тела запроса
        update_data = await request.json()
        update = Update(**update_data)

        logger.info(
            f"[TELEGRAM_WEBHOOK] Received update: "
            f"type={update.event_type}, "
            f"update_id={update.update_id}"
        )

        # Обрабатываем update через dispatcher
        await dp.feed_update(bot=bot, update=update)

        return {"ok": True}

    except Exception as e:
        logger.error(
            f"[TELEGRAM_WEBHOOK] Error processing update: {e}",
            exc_info=True,
        )
        return {"ok": False, "error": str(e)}


@router.get("/health")
async def telegram_health() -> dict:
    """
    Health check endpoint для Telegram webhook
    """
    return {"status": "ok", "service": "telegram_webhook"}
