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


class MessageDecryptRequest(BaseModel):
    user_id: str
    password: str


class MessageDecryptResponse(BaseModel):
    message_id: str
    plaintext: str


class GroupMessageCreate(BaseModel):
    sender_id: str
    group_id: str
    recipient_ids: list[str]
    plaintext: str


class GroupMessageResponse(BaseModel):
    id: str
    sender_id: str
    recipient_id: str | None
    group_id: str
    ciphertext: str
    nonce: str
    auth_tag: str
    encrypted_keys_count: int
    created_at: datetime