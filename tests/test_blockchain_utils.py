# tests/test_blockchain_utils.py

import pytest

from src.crypto.signatures import hash_message_sha256
from src.blockchain.blockchain_utils import (
    calculate_block_hash,
    is_valid_proof,
    mine_block,
    validate_block_hash,
)


def test_calculate_block_hash_is_deterministic():
    message_hash = hash_message_sha256("Mensaje registrado en blockchain")
    previous_hash = "0" * 64

    hash_1 = calculate_block_hash(
        index=1,
        timestamp="2026-05-18T10:00:00",
        sender_id="user-a",
        recipient_id="user-b",
        message_hash=message_hash,
        previous_hash=previous_hash,
        nonce=123
    )

    hash_2 = calculate_block_hash(
        index=1,
        timestamp="2026-05-18T10:00:00",
        sender_id="user-a",
        recipient_id="user-b",
        message_hash=message_hash,
        previous_hash=previous_hash,
        nonce=123
    )

    assert hash_1 == hash_2
    assert len(hash_1) == 64


def test_block_hash_changes_when_nonce_changes():
    message_hash = hash_message_sha256("Mensaje registrado en blockchain")
    previous_hash = "0" * 64

    hash_1 = calculate_block_hash(
        index=1,
        timestamp="2026-05-18T10:00:00",
        sender_id="user-a",
        recipient_id="user-b",
        message_hash=message_hash,
        previous_hash=previous_hash,
        nonce=1
    )

    hash_2 = calculate_block_hash(
        index=1,
        timestamp="2026-05-18T10:00:00",
        sender_id="user-a",
        recipient_id="user-b",
        message_hash=message_hash,
        previous_hash=previous_hash,
        nonce=2
    )

    assert hash_1 != hash_2


def test_mine_block_finds_valid_proof():
    message_hash = hash_message_sha256("Mensaje para minar bloque")
    previous_hash = "0" * 64

    nonce, block_hash = mine_block(
        index=1,
        timestamp="2026-05-18T10:00:00",
        sender_id="user-a",
        recipient_id="user-b",
        message_hash=message_hash,
        previous_hash=previous_hash,
        difficulty=2
    )

    assert isinstance(nonce, int)
    assert block_hash.startswith("00")
    assert is_valid_proof(block_hash, difficulty=2) is True


def test_validate_block_hash_returns_true_for_valid_block():
    message_hash = hash_message_sha256("Mensaje válido")
    previous_hash = "0" * 64

    nonce, block_hash = mine_block(
        index=1,
        timestamp="2026-05-18T10:00:00",
        sender_id="user-a",
        recipient_id="user-b",
        message_hash=message_hash,
        previous_hash=previous_hash,
        difficulty=2
    )

    is_valid = validate_block_hash(
        index=1,
        timestamp="2026-05-18T10:00:00",
        sender_id="user-a",
        recipient_id="user-b",
        message_hash=message_hash,
        previous_hash=previous_hash,
        nonce=nonce,
        expected_hash=block_hash,
        difficulty=2
    )

    assert is_valid is True


def test_validate_block_hash_returns_false_if_message_hash_changes():
    original_message_hash = hash_message_sha256("Mensaje original")
    tampered_message_hash = hash_message_sha256("Mensaje alterado")
    previous_hash = "0" * 64

    nonce, block_hash = mine_block(
        index=1,
        timestamp="2026-05-18T10:00:00",
        sender_id="user-a",
        recipient_id="user-b",
        message_hash=original_message_hash,
        previous_hash=previous_hash,
        difficulty=2
    )

    is_valid = validate_block_hash(
        index=1,
        timestamp="2026-05-18T10:00:00",
        sender_id="user-a",
        recipient_id="user-b",
        message_hash=tampered_message_hash,
        previous_hash=previous_hash,
        nonce=nonce,
        expected_hash=block_hash,
        difficulty=2
    )

    assert is_valid is False


def test_calculate_block_hash_rejects_invalid_previous_hash():
    message_hash = hash_message_sha256("Mensaje")

    with pytest.raises(ValueError):
        calculate_block_hash(
            index=1,
            timestamp="2026-05-18T10:00:00",
            sender_id="user-a",
            recipient_id="user-b",
            message_hash=message_hash,
            previous_hash="hash-invalido",
            nonce=1
        )