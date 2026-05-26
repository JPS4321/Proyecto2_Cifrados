# tests/test_totp_utils.py

import pyotp

from src.crypto.totp_utils import (
    build_totp_uri,
    generate_totp_secret,
    verify_totp_code,
)


def test_generate_totp_secret_returns_valid_secret():
    secret = generate_totp_secret()

    assert isinstance(secret, str)
    assert len(secret) >= 16


def test_build_totp_uri_contains_email_and_issuer():
    secret = generate_totp_secret()
    uri = build_totp_uri("user@test.com", secret)

    assert uri.startswith("otpauth://totp/")
    assert "user%40test.com" in uri or "user@test.com" in uri
    assert "VaultChain" in uri


def test_verify_totp_code_accepts_valid_code():
    secret = generate_totp_secret()
    code = pyotp.TOTP(secret).now()

    assert verify_totp_code(secret, code) is True


def test_verify_totp_code_rejects_invalid_code():
    secret = generate_totp_secret()

    assert verify_totp_code(secret, "000000") is False


def test_verify_totp_code_rejects_bad_format():
    secret = generate_totp_secret()

    assert verify_totp_code(secret, "abc123") is False
    assert verify_totp_code(secret, "123") is False
    assert verify_totp_code(secret, "") is False