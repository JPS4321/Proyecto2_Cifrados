from sqlalchemy import Column, String, Text, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID

from src.database import Base


class User(Base):
    __tablename__ = "usuarios"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    email = Column(String(255), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)

    password_hash = Column(String(255), nullable=False)

    public_key = Column(Text, nullable=False)
    encrypted_private_key = Column(Text, nullable=False)

    totp_secret = Column(String(32))

    created_at = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP")
    )