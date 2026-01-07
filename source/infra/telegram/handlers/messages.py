from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from dishka import FromDishka

from source.config.logging import logger

router = Router(name="messages")


@router.message(F.text)
async def handle_text_message(
    message: Message,
) -> None:
    """
    Обработчик текстовых сообщений от пользователей.
    Направляет сообщение в систему агентов для обработки.
    """
    if message and message.from_user:
        logger.info(
            f"[TELEGRAM] Text message from user_id={message.from_user.id}, "
            f"text_length={len(message.text or '')}"
        )
    else:
        logger.debug("[TELEGRAM] /start error - message.from_user is None")

    # TODO: Интеграция с AgentsInteractor
    # 1. Получить пользователя из БД по telegram_id
    # 2. Создать State для агентов
    # 3. Вызвать AgentsInteractor для обработки
    # 4. Отправить результат пользователю

    await message.answer(
        "💬 Получил ваше сообщение!\n(Обработка агентами в разработке)"
    )


@router.callback_query(F.data.startswith("confirm_"))
async def handle_confirmation_callback(
    callback: CallbackQuery,
) -> None:
    """
    Обработчик callback для подтверждений.
    Формат: confirm_{deal_id}_{action}
    """
    logger.info(
        f"[TELEGRAM] Confirmation callback from user_id={callback.from_user.id}, "
        f"data={callback.data}"
    )

    # TODO: Обработка подтверждений через агента
    await callback.answer("Подтверждение принято!")
    await callback.message.edit_text(f"✅ Подтверждено\n(Обработка в разработке)")


@router.callback_query(F.data.startswith("edit_"))
async def handle_edit_callback(
    callback: CallbackQuery,
) -> None:
    """
    Обработчик callback для редактирования.
    Формат: edit_{deal_id}_{field}
    """
    logger.info(
        f"[TELEGRAM] Edit callback from user_id={callback.from_user.id}, "
        f"data={callback.data}"
    )

    # TODO: Обработка редактирования через агента
    await callback.answer()
    await callback.message.answer("✏️ Начинаем редактирование\n(Функция в разработке)")


@router.callback_query(F.data.startswith("view_"))
async def handle_view_callback(
    callback: CallbackQuery,
) -> None:
    """
    Обработчик callback для просмотра деталей.
    Формат: view_{type}_{id}
    """
    logger.info(
        f"[TELEGRAM] View callback from user_id={callback.from_user.id}, "
        f"data={callback.data}"
    )

    # TODO: Получение и отображение деталей
    await callback.answer()
    await callback.message.answer("👁️ Загружаю детали...\n(Функция в разработке)")


@router.callback_query()
async def handle_unknown_callback(
    callback: CallbackQuery,
) -> None:
    """
    Обработчик неизвестных callback
    """
    logger.warning(
        f"[TELEGRAM] Unknown callback from user_id={callback.from_user.id}, "
        f"data={callback.data}"
    )

    await callback.answer("Неизвестная команда", show_alert=True)
