from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from dishka import FromDishka

from source.config.logging import logger
from source.api.agents.interactor_abc import AgentsInteractorAbc
from source.schemas.pydantic.agents import State
from source.db.models.telegram_user import TelegramUser

router = Router(name="messages")


@router.message(F.text)
async def handle_text_message(
    message: Message,
    telegram_user: TelegramUser,
    agents_interactor: FromDishka[AgentsInteractorAbc],
) -> None:
    """
    Обработчик текстовых сообщений от пользователей.
    Направляет сообщение в систему агентов для обработки.
    """
    if not message or not message.from_user or not message.text:
        logger.warning("[TELEGRAM] Invalid message: missing required fields")
        return

    logger.info(
        f"[TELEGRAM] Text message from user_id={message.from_user.id}, "
        f"text_length={len(message.text)}"
    )

    # Создаем State для агентов
    state = State(
        telegram_user_id=telegram_user.id,
        telegram_chat_id=message.chat.id,
        crm_user_id=telegram_user.crm_user_id,
        user_role=telegram_user.role.value,
        user_input=message.text,
        message_id=message.message_id,
    )

    try:
        # Вызываем AgentsInteractor для обработки
        result_state = await agents_interactor(state=state)

        # Отправляем результат пользователю
        if result_state.result:
            await message.answer(text=result_state.result)
        else:
            await message.answer(text="✅ Запрос обработан")

    except Exception as e:
        logger.error(f"[TELEGRAM] Error processing message: {e}", exc_info=True)
        await message.answer(text="❌ Произошла ошибка при обработке запроса. Попробуйте позже.")


@router.callback_query(F.data.startswith("confirm_"))
async def handle_confirmation_callback(
    callback: CallbackQuery,
) -> None:
    """
    Обработчик callback для подтверждений.
    Формат: confirm_{deal_id}_{action}
    """
    if callback and callback.from_user:
        logger.info(
            f"[TELEGRAM] Confirmation callback from user_id={callback.from_user.id}, "
            f"data={callback.data}"
        )
    else:
        logger.debug("[TELEGRAM] Callback error - callback.from_user is None")
        return

    # TODO: Обработка подтверждений через агента
    await callback.answer(text="Подтверждение принято!")

    # Проверяем что message это Message, а не InaccessibleMessage
    if callback.message and isinstance(callback.message, Message):
        try:
            await callback.message.edit_text(text="✅ Подтверждено\n(Обработка в разработке)")
        except Exception as e:
            logger.warning(f"[TELEGRAM] Failed to edit message: {e}")


@router.callback_query(F.data.startswith("edit_"))
async def handle_edit_callback(
    callback: CallbackQuery,
) -> None:
    """
    Обработчик callback для редактирования.
    Формат: edit_{deal_id}_{field}
    """
    if callback and callback.from_user:
        logger.info(
            f"[TELEGRAM] Edit callback from user_id={callback.from_user.id}, "
            f"data={callback.data}"
        )
    else:
        logger.debug("[TELEGRAM] Callback error - callback.from_user is None")
        return

    # TODO: Обработка редактирования через агента
    await callback.answer()

    # Проверяем что message это Message, а не InaccessibleMessage
    if callback.message and isinstance(callback.message, Message):
        try:
            await callback.message.answer(text="✏️ Начинаем редактирование\n(Функция в разработке)")
        except Exception as e:
            logger.warning(f"[TELEGRAM] Failed to send message: {e}")


@router.callback_query(F.data.startswith("view_"))
async def handle_view_callback(
    callback: CallbackQuery,
) -> None:
    """
    Обработчик callback для просмотра деталей.
    Формат: view_{type}_{id}
    """
    if callback and callback.from_user:
        logger.info(
            f"[TELEGRAM] View callback from user_id={callback.from_user.id}, "
            f"data={callback.data}"
        )
    else:
        logger.debug("[TELEGRAM] Callback error - callback.from_user is None")
        return

    # TODO: Получение и отображение деталей
    await callback.answer()

    # Проверяем что message это Message, а не InaccessibleMessage
    if callback.message and isinstance(callback.message, Message):
        try:
            await callback.message.answer(text="👁️ Загружаю детали...\n(Функция в разработке)")
        except Exception as e:
            logger.warning(f"[TELEGRAM] Failed to send message: {e}")


@router.callback_query()
async def handle_unknown_callback(
    callback: CallbackQuery,
) -> None:
    """
    Обработчик неизвестных callback
    """
    if callback and callback.from_user:
        logger.warning(
            f"[TELEGRAM] Unknown callback from user_id={callback.from_user.id}, "
            f"data={callback.data}"
        )
    else:
        logger.debug("[TELEGRAM] Callback error - callback.from_user is None")
        return

    await callback.answer(text="Неизвестная команда", show_alert=True)
