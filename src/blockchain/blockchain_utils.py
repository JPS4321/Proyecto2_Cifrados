# src/blockchain/blockchain_utils.py

import hashlib
from datetime import datetime
from typing import Optional, Tuple, Union


DEFAULT_DIFFICULTY = 4


def normalize_timestamp(timestamp: Union[str, datetime]) -> str:
    """
    Normaliza el timestamp para que el hash sea determinístico.
    """
    if isinstance(timestamp, datetime):
        return timestamp.isoformat()

    if isinstance(timestamp, str) and timestamp.strip():
        return timestamp

    raise ValueError("El timestamp debe ser datetime o string no vacío.")


def build_block_payload(
    index: int,
    timestamp: Union[str, datetime],
    sender_id: Optional[str],
    recipient_id: Optional[str],
    message_hash: str,
    previous_hash: str,
    nonce: int
) -> str:
    """
    Construye el contenido que se usará para calcular el hash del bloque.

    La estructura respeta la idea:
    SHA-256(indice + timestamp + datos + previous_hash + nonce)
    """
    if index < 0:
        raise ValueError("El índice del bloque no puede ser negativo.")

    if not isinstance(message_hash, str) or len(message_hash) != 64:
        raise ValueError("message_hash debe ser un SHA-256 hexadecimal de 64 caracteres.")

    if not isinstance(previous_hash, str) or len(previous_hash) != 64:
        raise ValueError("previous_hash debe tener 64 caracteres.")

    if nonce < 0:
        raise ValueError("El nonce no puede ser negativo.")

    timestamp_value = normalize_timestamp(timestamp)

    sender_value = str(sender_id) if sender_id is not None else ""
    recipient_value = str(recipient_id) if recipient_id is not None else ""

    return (
        f"{index}|"
        f"{timestamp_value}|"
        f"{sender_value}|"
        f"{recipient_value}|"
        f"{message_hash}|"
        f"{previous_hash}|"
        f"{nonce}"
    )


def calculate_block_hash(
    index: int,
    timestamp: Union[str, datetime],
    sender_id: Optional[str],
    recipient_id: Optional[str],
    message_hash: str,
    previous_hash: str,
    nonce: int
) -> str:
    """
    Calcula el hash SHA-256 de un bloque.
    """
    payload = build_block_payload(
        index=index,
        timestamp=timestamp,
        sender_id=sender_id,
        recipient_id=recipient_id,
        message_hash=message_hash,
        previous_hash=previous_hash,
        nonce=nonce
    )

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def is_valid_proof(block_hash: str, difficulty: int = DEFAULT_DIFFICULTY) -> bool:
    """
    Valida si un hash cumple con el proof-of-work simplificado.
    """
    if difficulty < 1:
        raise ValueError("La dificultad debe ser mayor o igual a 1.")

    return block_hash.startswith("0" * difficulty)


def mine_block(
    index: int,
    timestamp: Union[str, datetime],
    sender_id: Optional[str],
    recipient_id: Optional[str],
    message_hash: str,
    previous_hash: str,
    difficulty: int = DEFAULT_DIFFICULTY
) -> Tuple[int, str]:
    """
    Busca un nonce que produzca un hash válido.

    Retorna:
        (nonce, hash)
    """
    nonce = 0

    while True:
        block_hash = calculate_block_hash(
            index=index,
            timestamp=timestamp,
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_hash=message_hash,
            previous_hash=previous_hash,
            nonce=nonce
        )

        if is_valid_proof(block_hash, difficulty):
            return nonce, block_hash

        nonce += 1


def validate_block_hash(
    index: int,
    timestamp: Union[str, datetime],
    sender_id: Optional[str],
    recipient_id: Optional[str],
    message_hash: str,
    previous_hash: str,
    nonce: int,
    expected_hash: str,
    difficulty: int = DEFAULT_DIFFICULTY
) -> bool:
    """
    Recalcula el hash de un bloque y verifica que coincida con el hash almacenado.
    """
    calculated_hash = calculate_block_hash(
        index=index,
        timestamp=timestamp,
        sender_id=sender_id,
        recipient_id=recipient_id,
        message_hash=message_hash,
        previous_hash=previous_hash,
        nonce=nonce
    )

    return calculated_hash == expected_hash and is_valid_proof(
        block_hash=expected_hash,
        difficulty=difficulty
    )