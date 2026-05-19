from sqlalchemy import (
    Column,
    Integer,
    String,
    TIMESTAMP,
    text
)

from sqlalchemy.dialects.postgresql import UUID

from src.database import Base


class Block(Base):
    __tablename__ = "blockchain"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    index = Column(
        Integer,
        nullable=False,
        unique=True
    )

    timestamp = Column(
        TIMESTAMP,
        nullable=False
    )

    sender_id = Column(
        UUID(as_uuid=True),
        nullable=True
    )

    recipient_id = Column(
        UUID(as_uuid=True),
        nullable=True
    )

    message_hash = Column(
        String(64),
        nullable=False
    )

    previous_hash = Column(
        String(64),
        nullable=False
    )

    nonce = Column(
        Integer,
        nullable=False
    )

    hash = Column(
        String(64),
        nullable=False
    )