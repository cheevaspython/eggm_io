from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, DateTime, Float, Boolean, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ENUM
from uuid6 import UUID
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from source.db.models.base import Base
from source.db.models.choises.deal_status import ApplicationStatus
from source.db.models.mixins.create_update import CreateUpdateMixin
from source.db.models.mixins.id_int_pk import UUIDPkMixin


class Application(Base, UUIDPkMixin, CreateUpdateMixin):
    """
    Локальная модель заявки (синхронизируется с Django CRM).
    Может быть заявка от покупателя или продавца.
    """

    __tablename__ = "applications"  # type: ignore

    # Связь с CRM
    crm_application_id: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        nullable=False,
        index=True,
        comment="ID заявки в Django CRM",
    )
    application_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Тип заявки: buyer или seller",
    )

    # Статус
    status: Mapped[ApplicationStatus] = mapped_column(
        ENUM(ApplicationStatus, name="applicationstatus"),
        default=ApplicationStatus.active,
        nullable=False,
        comment="Статус заявки",
    )

    # Пользователи
    owner_crm_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="ID автора заявки в CRM",
    )
    telegram_user_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="ID пользователя Telegram",
    )

    # Клиент
    client_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Название клиента (покупатель или продавец)",
    )
    client_crm_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="ID клиента в CRM",
    )

    # Даты
    delivery_date_from: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Дата доставки с",
    )
    delivery_date_to: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Дата доставки по",
    )

    # Товар (упрощенная версия)
    total_eggs_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Общее количество яиц",
    )
    price_per_egg: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Средняя цена за яйцо",
    )

    # Адреса
    address: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Адрес погрузки/разгрузки",
    )

    # Подтверждения
    is_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Подтверждена ли заявка",
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Дата подтверждения",
    )

    # Связь со сделкой
    deal_crm_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="ID сделки в CRM, если заявка перешла в сделку",
    )

    # Дополнительные данные
    comment: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Комментарий к заявке",
    )
    additional_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Дополнительные данные из CRM (JSON)",
    )

    # Синхронизация
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Последняя синхронизация с CRM",
    )

    def __repr__(self) -> str:
        return f"<Application(crm_id={self.crm_application_id}, type={self.application_type}, owner={self.owner_crm_id})>"
