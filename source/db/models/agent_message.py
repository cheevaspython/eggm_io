from typing import Optional

from uuid6 import UUID
from sqlalchemy import TEXT, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ENUM
from sqlalchemy.orm import Mapped, mapped_column

from source.db.models import Base
from source.db.models.choises.enum import (
    InlineStatusChoises,
    MessageTypeChoises,
)
from source.db.models.mixins.create_update import CreateUpdateMixin
from source.db.models.mixins.id_int_pk import UUIDPkMixin
from source.types.io_token import TokenOut


class AgentMessage(Base, UUIDPkMixin, CreateUpdateMixin):
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    response_text: Mapped[str] = mapped_column(
        TEXT,
        nullable=True,
    )
    question: Mapped[str] = mapped_column(
        TEXT,
        nullable=True,
    )
    inline: Mapped[Optional[InlineStatusChoises]] = mapped_column(
        ENUM(InlineStatusChoises, name="inlinestatuschoises"),
        nullable=True,
    )
    message_type: Mapped[MessageTypeChoises] = mapped_column(
        ENUM(MessageTypeChoises, name="messagetypechoises"),
        default=MessageTypeChoises.simple_message,
        nullable=False,
    )
    token_out: Mapped[TokenOut] = mapped_column(
        default=0,
        server_default=text("0"),
        nullable=False,
    )
