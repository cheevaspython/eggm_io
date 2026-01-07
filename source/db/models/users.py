from sqlalchemy.orm import Mapped, mapped_column

from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy import (
    Integer,
    String,
    text,
)

from source.db.models.base import Base
from source.db.models.choises.enum import PermissionStatus, RoleTypeChoises
from source.db.models.mixins.create_update import CreateUpdateMixin
from source.db.models.mixins.id_int_pk import UUIDPkMixin


class User(Base, UUIDPkMixin, CreateUpdateMixin):
    __tablename__ = "users"  # type: ignore

    role: Mapped[RoleTypeChoises] = mapped_column(
        ENUM(RoleTypeChoises, name="roletypechoises"),
        default=RoleTypeChoises.guest,
        nullable=False,
    )
    permission_status: Mapped[PermissionStatus] = mapped_column(
        ENUM(PermissionStatus, name="permissionstatus"),
        default=PermissionStatus.standart,
        nullable=False,
    )

    phone_number: Mapped[str] = mapped_column(
        String(20),
        nullable=True,
        unique=True,
    )
    master_password: Mapped[str] = mapped_column(
        String(30),
        nullable=True,
        unique=True,
    )
    text_style: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default=text("1"),
    )
