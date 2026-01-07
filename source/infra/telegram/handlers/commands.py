from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from source.config.logging import logger

router = Router(name="commands")


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """
    Обработчик команды /start
    """
    if message and message.from_user:
        logger.info(
            f"[TELEGRAM] /start from user_id={message.from_user.id}, "
            f"username={message.from_user.username}"
        )
    else:
        logger.debug("[TELEGRAM] /start error - message.from_user is None")

    welcome_text = (
        "👋 Добро пожаловать в систему управления сделками!\n\n"
        "Я помогу вам:\n"
        "• Получать напоминания о важных датах\n"
        "• Подтверждать данные сделок\n"
        "• Редактировать заявки и сделки\n"
        "• Получать аналитику\n\n"
        "Используйте /help для просмотра всех команд"
    )

    await message.answer(welcome_text)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """
    Обработчик команды /help
    """
    if message and message.from_user:
        logger.info(f"[TELEGRAM] /help from user_id={message.from_user.id}")
    else:
        logger.debug("[TELEGRAM] /start error - message.from_user is None")

    help_text = (
        "📋 <b>Доступные команды:</b>\n\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n"
        "/deals - Показать мои сделки\n"
        "/applications - Показать мои заявки\n"
        "/reminders - Показать напоминания\n"
        "/stats - Моя статистика\n\n"
        "💬 Вы также можете писать мне свободные вопросы, "
        "и я постараюсь помочь!"
    )

    await message.answer(help_text)


@router.message(Command("deals"))
async def cmd_deals(message: Message) -> None:
    """
    Обработчик команды /deals
    Показывает список сделок пользователя
    """

    if message and message.from_user:
        logger.info(f"[TELEGRAM] /deals from user_id={message.from_user.id}")
    else:
        logger.debug("[TELEGRAM] /start error - message.from_user is None")

    # TODO: Интеграция с агентом для получения списка сделок
    await message.answer("📊 Загружаю ваши сделки...\n(Функция в разработке)")


@router.message(Command("applications"))
async def cmd_applications(message: Message) -> None:
    """
    Обработчик команды /applications
    Показывает список заявок пользователя
    """
    if message and message.from_user:
        logger.info(f"[TELEGRAM] /applications from user_id={message.from_user.id}")
    else:
        logger.debug("[TELEGRAM] /start error - message.from_user is None")

    # TODO: Интеграция с агентом для получения списка заявок
    await message.answer("📝 Загружаю ваши заявки...\n(Функция в разработке)")


@router.message(Command("reminders"))
async def cmd_reminders(message: Message) -> None:
    """
    Обработчик команды /reminders
    Показывает активные напоминания
    """
    if message and message.from_user:
        logger.info(f"[TELEGRAM] /reminders from user_id={message.from_user.id}")
    else:
        logger.debug("[TELEGRAM] /start error - message.from_user is None")

    # TODO: Интеграция с агентом напоминаний
    await message.answer("⏰ Загружаю ваши напоминания...\n(Функция в разработке)")


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """
    Обработчик команды /stats
    Показывает статистику пользователя
    """
    if message and message.from_user:
        logger.info(f"[TELEGRAM] /stats from user_id={message.from_user.id}")
    else:
        logger.debug("[TELEGRAM] /start error - message.from_user is None")

    # TODO: Интеграция с агентом аналитики
    await message.answer("📈 Загружаю вашу статистику...\n(Функция в разработке)")
