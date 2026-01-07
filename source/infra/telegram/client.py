from aiohttp import ClientSession
from typing import Any

from source.config.logging import logger


class TelegramClient:
    """Клиент для отправки сообщений через Telegram Bot API."""

    def __init__(
        self,
        bot_token: str,
        chat_id: int,
        session: ClientSession,
    ) -> None:
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._session = session
        self._base_url = f"https://api.telegram.org/bot{bot_token}"

    async def send_message(
        self,
        text: str = "",
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = True,
    ) -> dict[str, Any]:
        """Отправить сообщение в чат/канал."""
        url = f"{self._base_url}/sendMessage"
        payload = {
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        }

        logger.info(
            f"[TELEGRAM CLIENT] Sending message: url={url}, chat_id={self._chat_id}, "
            f"text_length={len(text)}, parse_mode={parse_mode}"
        )

        return await self._send_with_session(
            session=self._session,
            url=url,
            payload=payload,
            chat_id=self._chat_id,
        )

    async def _send_with_session(
        self,
        session: ClientSession,
        url: str,
        payload: dict,
        chat_id: int,
    ) -> dict[str, Any]:
        """Отправка через существующую сессию."""
        logger.info(f"[TELEGRAM CLIENT] Making POST request to {url}")
        async with session.post(url, json=payload) as response:
            logger.info(
                f"[TELEGRAM CLIENT] Response received: status={response.status}"
            )
            response_data = await response.json()
            logger.info(
                f"[TELEGRAM CLIENT] Response data parsed: ok={response_data.get('ok')}"
            )

            if not response_data.get("ok"):
                error_description = response_data.get("description", "Unknown error")
                logger.error(
                    f"Telegram API error: {error_description}",
                    extra={
                        "chat_id": chat_id,
                        "error_code": response_data.get("error_code"),
                    },
                )
                raise TelegramAPIError(f"Failed to send message: {error_description}")

            logger.info(
                f"Message sent successfully to chat {chat_id}",
                extra={
                    "message_id": response_data["result"]["message_id"],
                    "chat_id": chat_id,
                },
            )
            return response_data["result"]


class TelegramAPIError(Exception):
    """Ошибка при работе с Telegram API."""

    pass
