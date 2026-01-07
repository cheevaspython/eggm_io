from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from uuid6 import UUID
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from source.db.models.base import Base
from source.db.models.mixins.create_update import CreateUpdateMixin
from source.db.models.mixins.id_int_pk import UUIDPkMixin


class DealReminder(Base, UUIDPkMixin, CreateUpdateMixin):
    """
    Модель для хранения напоминаний по сделкам.
    Используется для отправки уведомлений менеджерам о важных датах.
    """

    __tablename__ = "deal_reminders"  # type: ignore

    # Связь со сделкой
    deal_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="ID сделки (ForeignKey на deals)",
    )
    crm_deal_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="ID сделки в CRM для быстрого доступа",
    )

    # Пользователь
    telegram_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="ID пользователя Telegram для отправки",
    )

    # Тип напоминания
    reminder_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Тип: loading, unloading, payment, confirmation",
    )

    # Дата и время напоминания
    remind_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Когда отправить напоминание",
    )
    target_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Целевая дата события (погрузка, оплата и т.д.)",
    )

    # Статус напоминания
    is_sent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Отправлено ли напоминание",
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Когда было отправлено",
    )

    # Дополнительная информация
    message_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Текст сообщения напоминания",
    )
    additional_info: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Дополнительная информация",
    )

    # Повторная отправка
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Количество попыток отправки",
    )
    last_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Последняя попытка отправки",
    )

    def __repr__(self) -> str:
        return f"<DealReminder(deal_id={self.crm_deal_id}, type={self.reminder_type}, remind_at={self.remind_at})>"
