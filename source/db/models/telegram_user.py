from sqlalchemy import BigInteger, String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ENUM

from source.db.models.base import Base
from source.db.models.choises.enum import RoleTypeChoises
from source.db.models.mixins.create_update import CreateUpdateMixin
from source.db.models.mixins.id_int_pk import UUIDPkMixin


class TelegramUser(Base, UUIDPkMixin, CreateUpdateMixin):
    """
    Модель для связи пользователя Telegram с пользователем CRM.
    Хранит telegram_id и связывает с user_id в Django CRM.
    """

    __tablename__ = "telegram_users"  # type: ignore

    telegram_id = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True,
        comment="Telegram ID пользователя",
    )
    crm_user_id = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="ID пользователя в Django CRM",
    )
    username: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        comment="Username в Telegram",
    )
    first_name: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        comment="Имя пользователя",
    )
    last_name: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        comment="Фамилия пользователя",
    )
    role: Mapped[RoleTypeChoises] = mapped_column(
        ENUM(RoleTypeChoises, name="roletypechoises"),
        nullable=False,
        comment="Роль пользователя в системе",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Активен ли пользователь",
    )
    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Заблокирован ли пользователь",
    )

    def __repr__(self) -> str:
        return f"<TelegramUser(telegram_id={self.telegram_id}, crm_user_id={self.crm_user_id}, role={self.role.value})>"
