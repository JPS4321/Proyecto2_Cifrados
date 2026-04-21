# tests/test_crypto.py

from src.crypto.crypto_utils import (
    generate_rsa_keypair,
    encrypt_private_key,
    decrypt_private_key,
    generate_and_protect_keypair,
)

def test_generate_rsa_keypair_returns_pem_strings():
    private_key, public_key = generate_rsa_keypair()

    assert "BEGIN PRIVATE KEY" in private_key
    assert "BEGIN PUBLIC KEY" in public_key


def test_encrypt_and_decrypt_private_key_successfully():
    password = "PasswordSegura123!"
    private_key, _ = generate_rsa_keypair()

    encrypted = encrypt_private_key(private_key, password)
    decrypted = decrypt_private_key(encrypted, password)

    assert decrypted == private_key


def test_generate_and_protect_keypair_returns_expected_outputs():
    password = "OtraPassword123!"
    public_key, encrypted_private_key = generate_and_protect_keypair(password)

    assert "BEGIN PUBLIC KEY" in public_key
    assert isinstance(encrypted_private_key, str)
    assert "ciphertext" in encrypted_private_key