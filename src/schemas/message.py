from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class MessageCreate(BaseModel):
    sender_id: UUID
    recipient_id: UUID
    plaintext: str


class MessageResponse(BaseModel):
    id: UUID
    sender_id: UUID
    recipient_id: UUID | None
    group_id: UUID | None
    ciphertext: str
    nonce: str
    auth_tag: str
    created_at: datetime    


class MessageWithKeyResponse(MessageResponse):
    encrypted_key: str