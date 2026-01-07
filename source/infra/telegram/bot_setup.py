from aiogram import Dispatcher, Bot
from aiogram.webhook.aiohttp_server import SimpleRequestHandler

from source.infra.telegram.handlers import commands, messages
from source.infra.telegram.middleware import AuthMiddleware
from source.config.logging import logger


def setup_dispatcher() -> Dispatcher:
    """
    Настройка dispatcher для обработки сообщений
    """
    dp = Dispatcher()

    # Регистрируем роутеры
    dp.include_router(router=commands.router)
    dp.include_router(router=messages.router)

    # Регистрируем middleware
    # AuthMiddleware должен проверять пользователя перед обработкой
    dp.message.middleware(middleware=AuthMiddleware())
    dp.callback_query.middleware(middleware=AuthMiddleware())

    logger.info("[BOT_SETUP] Dispatcher configured successfully")

    return dp


def create_webhook_handler(
    bot: Bot,
    dispatcher: Dispatcher,
) -> SimpleRequestHandler:
    """
    Создание webhook handler для обработки запросов от Telegram
    """
    return SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
    )
