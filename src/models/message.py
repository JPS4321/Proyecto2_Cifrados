from sqlalchemy import Column, Text, String, TIMESTAMP, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from src.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

    sender_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    group_id = Column(UUID(as_uuid=True), nullable=True)

    ciphertext = Column(Text, nullable=False)
    nonce = Column(String, nullable=False)
    auth_tag = Column(String, nullable=False)

    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))