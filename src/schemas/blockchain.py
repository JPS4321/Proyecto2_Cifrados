from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class BlockResponse(BaseModel):
    id: UUID
    index: int
    timestamp: datetime
    sender_id: UUID | None
    recipient_id: UUID | None
    message_hash: str
    previous_hash: str
    nonce: int
    hash: str


class BlockchainVerifyResponse(BaseModel):
    valid: bool
    blocks_checked: int
    warning: str | None = None