# tests/test_signatures.py

import base64

import pytest

from src.crypto.crypto_utils import generate_rsa_keypair
from src.crypto.signatures import (
    hash_message_sha256,
    sign_message_hash,
    verify_message_signature,
    sign_plaintext_message,
    verify_plaintext_message,
)


def _tamper_base64_value(value_b64: str) -> str:
    """
    Modifica una firma Base64 para probar detección de alteración.
    """
    raw = bytearray(base64.b64decode(value_b64.encode("utf-8")))
    raw[0] ^= 1
    return base64.b64encode(bytes(raw)).decode("utf-8")


def test_hash_message_sha256_returns_64_hex_chars():
    plaintext = "Mensaje importante para firmar"

    message_hash = hash_message_sha256(plaintext)

    assert isinstance(message_hash, str)
    assert len(message_hash) == 64
    int(message_hash, 16)


def test_valid_signature_verification():
    private_key_pem, public_key_pem = generate_rsa_keypair()
    plaintext = "Mensaje original firmado"

    message_hash = hash_message_sha256(plaintext)
    signature = sign_message_hash(private_key_pem, message_hash)

    is_valid = verify_message_signature(
        public_key_pem=public_key_pem,
        message_hash_hex=message_hash,
        signature_b64=signature
    )

    assert is_valid is True


def test_invalid_signature_when_message_changes():
    private_key_pem, public_key_pem = generate_rsa_keypair()

    original_plaintext = "Mensaje original"
    altered_plaintext = "Mensaje alterado"

    original_hash = hash_message_sha256(original_plaintext)
    altered_hash = hash_message_sha256(altered_plaintext)

    signature = sign_message_hash(private_key_pem, original_hash)

    is_valid = verify_message_signature(
        public_key_pem=public_key_pem,
        message_hash_hex=altered_hash,
        signature_b64=signature
    )

    assert is_valid is False


def test_invalid_signature_when_signature_changes():
    private_key_pem, public_key_pem = generate_rsa_keypair()
    plaintext = "Mensaje con firma manipulada"

    message_hash = hash_message_sha256(plaintext)
    signature = sign_message_hash(private_key_pem, message_hash)

    tampered_signature = _tamper_base64_value(signature)

    is_valid = verify_message_signature(
        public_key_pem=public_key_pem,
        message_hash_hex=message_hash,
        signature_b64=tampered_signature
    )

    assert is_valid is False


def test_sign_and_verify_plaintext_message_successfully():
    private_key_pem, public_key_pem = generate_rsa_keypair()
    plaintext = "Mensaje usando funciones de alto nivel"

    signed_payload = sign_plaintext_message(
        private_key_pem=private_key_pem,
        plaintext=plaintext
    )

    is_valid = verify_plaintext_message(
        public_key_pem=public_key_pem,
        plaintext=plaintext,
        signature_b64=signed_payload["signature"]
    )

    assert "message_hash" in signed_payload
    assert "signature" in signed_payload
    assert is_valid is True


def test_hash_message_rejects_empty_plaintext():
    with pytest.raises(ValueError):
        hash_message_sha256("")