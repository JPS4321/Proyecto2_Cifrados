from datetime import datetime

from src.database import SessionLocal

from src.crud.blockchain_crud import (
    create_block,
    get_all_blocks
)


db = SessionLocal()

try:
    block = create_block(db, {
        "index": 0,
        "timestamp": datetime.utcnow(),
        "sender_id": None,
        "recipient_id": None,
        "message_hash": "abc123",
        "previous_hash": "000000",
        "nonce": 100,
        "hash": "0000ffff"
    })

    print("Bloque creado:")
    print(block.id)

    blocks = get_all_blocks(db)

    print("Cantidad de bloques:")
    print(len(blocks))

finally:
    db.close()