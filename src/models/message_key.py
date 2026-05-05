from sqlalchemy import Column, Text, TIMESTAMP, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from src.database import Base


class MessageKey(Base):
    __tablename__ = "message_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    encrypted_key = Column(Text, nullable=False)

    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))