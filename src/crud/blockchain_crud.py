from sqlalchemy.orm import Session

from src.models.block import Block


# Obtiene el último bloque de la cadena
def get_last_block(db: Session):
    return (
        db.query(Block)
        .order_by(Block.index.desc())
        .first()
    )


# Obtiene todos los bloques
def get_all_blocks(db: Session):
    return (
        db.query(Block)
        .order_by(Block.index.asc())
        .all()
    )


# Crea un nuevo bloque
def create_block(db: Session, block_data: dict):
    block = Block(**block_data)

    db.add(block)

    db.commit()

    db.refresh(block)

    return block


# Cuenta cuántos bloques existen
def count_blocks(db: Session):
    return db.query(Block).count()


# Busca un bloque por ID
def get_block_by_id(db: Session, block_id):
    return (
        db.query(Block)
        .filter(Block.id == block_id)
        .first()
    )