from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, DateTime, Float, Boolean, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ENUM
from uuid6 import UUID
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from source.db.models.base import Base
from source.db.models.choises.deal_status import DealStatus, DealDetailStatus
from source.db.models.mixins.create_update import CreateUpdateMixin
from source.db.models.mixins.id_int_pk import UUIDPkMixin


class Deal(Base, UUIDPkMixin, CreateUpdateMixin):
    """
    Локальная модель сделки (синхронизируется с Django CRM).
    Содержит основные поля для работы бота и напоминаний.
    """

    __tablename__ = "deals"  # type: ignore

    # Связь с CRM
    crm_deal_id: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        nullable=False,
        index=True,
        comment="ID сделки в Django CRM",
    )

    # Статусы
    status: Mapped[DealStatus] = mapped_column(
        ENUM(DealStatus, name="dealstatus"),
        nullable=False,
        comment="Основной статус сделки",
    )
    detail_status: Mapped[Optional[DealDetailStatus]] = mapped_column(
        ENUM(DealDetailStatus, name="dealdetailstatus"),
        nullable=True,
        comment="Детальный статус сделки",
    )

    # Пользователи
    owner_crm_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="ID автора сделки в CRM",
    )
    manager_crm_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="ID менеджера направления в CRM",
    )
    telegram_user_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="ID пользователя Telegram (ForeignKey на telegram_users)",
    )

    # Клиенты
    buyer_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Название покупателя",
    )
    seller_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Название продавца",
    )

    # Даты (важно для напоминаний)
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
    loading_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Дата погрузки",
    )
    unloading_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Дата разгрузки",
    )
    payment_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Дата оплаты",
    )

    # Финансы
    total_amount: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Общая сумма сделки",
    )
    paid_amount: Mapped[Optional[float]] = mapped_column(
        Float,
        default=0.0,
        nullable=True,
        comment="Оплаченная сумма",
    )

    # Подтверждения
    is_confirmed_by_manager: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Подтверждено менеджером",
    )
    is_confirmed_by_director: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Подтверждено директором",
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Дата подтверждения",
    )

    # Дополнительные поля
    comment: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Комментарий к сделке",
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
        return f"<Deal(crm_id={self.crm_deal_id}, status={self.status.value}, owner={self.owner_crm_id})>"
