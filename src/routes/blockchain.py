from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.blockchain.blockchain_utils import validate_block_hash
from src.crud.blockchain_crud import get_all_blocks
from src.database import get_db
from src.dependencies import get_current_user
from src.schemas.blockchain import BlockResponse, BlockchainVerifyResponse

router = APIRouter(prefix="/blockchain", tags=["blockchain"])


@router.get("", response_model=list[BlockResponse])
def get_blockchain(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_all_blocks(db)


@router.get("/verify", response_model=BlockchainVerifyResponse)
def verify_blockchain(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    blocks = get_all_blocks(db)

    if not blocks:
        return BlockchainVerifyResponse(
            valid=True,
            blocks_checked=0,
            warning="La blockchain está vacía.",
        )

    for index, block in enumerate(blocks):
        expected_previous_hash = "0" * 64 if index == 0 else blocks[index - 1].hash

        if block.previous_hash != expected_previous_hash:
            return BlockchainVerifyResponse(
                valid=False,
                blocks_checked=index + 1,
                warning=f"El bloque {block.index} no apunta al hash anterior correcto.",
            )

        is_valid = validate_block_hash(
            index=block.index,
            timestamp=block.timestamp,
            sender_id=str(block.sender_id) if block.sender_id else None,
            recipient_id=str(block.recipient_id) if block.recipient_id else None,
            message_hash=block.message_hash,
            previous_hash=block.previous_hash,
            nonce=block.nonce,
            expected_hash=block.hash,
        )

        if not is_valid:
            return BlockchainVerifyResponse(
                valid=False,
                blocks_checked=index + 1,
                warning=f"El bloque {block.index} tiene un hash inválido o no cumple proof-of-work.",
            )

    return BlockchainVerifyResponse(
        valid=True,
        blocks_checked=len(blocks),
        warning=None,
    )