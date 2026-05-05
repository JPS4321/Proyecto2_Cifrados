# tests/test_message_crypto.py

import base64
import pytest

from src.crypto.crypto_utils import generate_rsa_keypair
from src.crypto.message_crypto import (
    generate_aes_key,
    encrypt_aes_gcm,
    decrypt_aes_gcm,
    encrypt_aes_key_with_public_key,
    decrypt_aes_key_with_private_key,
    encrypt_message_for_recipient,
    decrypt_message_for_recipient,
    encrypt_message_for_group,
)


def _tamper_base64_value(value_b64: str) -> str:
    """
    Modifica un valor Base64 de forma controlada para probar integridad.
    """
    raw = bytearray(base64.b64decode(value_b64.encode("utf-8")))
    raw[0] ^= 1
    return base64.b64encode(bytes(raw)).decode("utf-8")


def test_aes_gcm_encrypts_and_decrypts_successfully():
    plaintext = "Mensaje secreto de prueba"
    aes_key = generate_aes_key()

    encrypted = encrypt_aes_gcm(plaintext, aes_key)
    decrypted = decrypt_aes_gcm(
        ciphertext_b64=encrypted["ciphertext"],
        nonce_b64=encrypted["nonce"],
        tag_b64=encrypted["auth_tag"],
        aes_key=aes_key
    )

    assert decrypted == plaintext
    assert encrypted["ciphertext"] != plaintext
    assert isinstance(encrypted["nonce"], str)
    assert isinstance(encrypted["auth_tag"], str)


def test_aes_gcm_generates_different_nonce_per_message():
    plaintext = "Mismo mensaje"
    aes_key = generate_aes_key()

    encrypted_1 = encrypt_aes_gcm(plaintext, aes_key)
    encrypted_2 = encrypt_aes_gcm(plaintext, aes_key)

    assert encrypted_1["nonce"] != encrypted_2["nonce"]
    assert encrypted_1["ciphertext"] != encrypted_2["ciphertext"]


def test_rsa_oaep_encrypts_and_decrypts_aes_key_successfully():
    private_key_pem, public_key_pem = generate_rsa_keypair()
    aes_key = generate_aes_key()

    encrypted_key = encrypt_aes_key_with_public_key(
        aes_key=aes_key,
        public_key_pem=public_key_pem
    )

    decrypted_key = decrypt_aes_key_with_private_key(
        encrypted_key_b64=encrypted_key,
        private_key_pem=private_key_pem
    )

    assert decrypted_key == aes_key
    assert isinstance(encrypted_key, str)


def test_hybrid_message_encryption_for_recipient_recovers_original_plaintext():
    private_key_pem, public_key_pem = generate_rsa_keypair()
    plaintext = "Este es un mensaje confidencial para un destinatario."

    encrypted = encrypt_message_for_recipient(
        plaintext=plaintext,
        recipient_public_key_pem=public_key_pem
    )

    decrypted = decrypt_message_for_recipient(
        ciphertext=encrypted["ciphertext"],
        encrypted_key=encrypted["encrypted_key"],
        nonce=encrypted["nonce"],
        auth_tag=encrypted["auth_tag"],
        recipient_private_key_pem=private_key_pem
    )

    assert decrypted == plaintext
    assert set(encrypted.keys()) == {
        "ciphertext",
        "encrypted_key",
        "nonce",
        "auth_tag"
    }


def test_group_message_encryption_generates_one_encrypted_key_per_recipient():
    private_key_1, public_key_1 = generate_rsa_keypair()
    private_key_2, public_key_2 = generate_rsa_keypair()
    private_key_3, public_key_3 = generate_rsa_keypair()

    recipients_public_keys = {
        "user-1": public_key_1,
        "user-2": public_key_2,
        "user-3": public_key_3,
    }

    plaintext = "Mensaje secreto para un grupo."

    encrypted_group_message = encrypt_message_for_group(
        plaintext=plaintext,
        recipients_public_keys=recipients_public_keys
    )

    assert "ciphertext" in encrypted_group_message
    assert "nonce" in encrypted_group_message
    assert "auth_tag" in encrypted_group_message
    assert "encrypted_keys" in encrypted_group_message
    assert len(encrypted_group_message["encrypted_keys"]) == 3

    private_keys_by_user = {
        "user-1": private_key_1,
        "user-2": private_key_2,
        "user-3": private_key_3,
    }

    for item in encrypted_group_message["encrypted_keys"]:
        user_id = item["user_id"]

        decrypted = decrypt_message_for_recipient(
            ciphertext=encrypted_group_message["ciphertext"],
            encrypted_key=item["encrypted_key"],
            nonce=encrypted_group_message["nonce"],
            auth_tag=encrypted_group_message["auth_tag"],
            recipient_private_key_pem=private_keys_by_user[user_id]
        )

        assert decrypted == plaintext


def test_decryption_fails_if_auth_tag_is_modified():
    private_key_pem, public_key_pem = generate_rsa_keypair()
    plaintext = "Mensaje que no debe permitir alteraciones."

    encrypted = encrypt_message_for_recipient(
        plaintext=plaintext,
        recipient_public_key_pem=public_key_pem
    )

    tampered_tag = _tamper_base64_value(encrypted["auth_tag"])

    with pytest.raises(Exception):
        decrypt_message_for_recipient(
            ciphertext=encrypted["ciphertext"],
            encrypted_key=encrypted["encrypted_key"],
            nonce=encrypted["nonce"],
            auth_tag=tampered_tag,
            recipient_private_key_pem=private_key_pem
        )