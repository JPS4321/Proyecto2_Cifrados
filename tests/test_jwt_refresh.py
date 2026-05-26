# tests/test_jwt_refresh.py

from src.core.jwt_utils import (
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
    JWTError,
)


def test_create_and_verify_access_token():
    token = create_access_token({"sub": "user-123", "email": "user@test.com"})
    payload = verify_access_token(token)

    assert payload["sub"] == "user-123"
    assert payload["email"] == "user@test.com"
    assert payload["type"] == "access"


def test_create_and_verify_refresh_token():
    token = create_refresh_token({"sub": "user-123", "email": "user@test.com"})
    payload = verify_refresh_token(token)

    assert payload["sub"] == "user-123"
    assert payload["email"] == "user@test.com"
    assert payload["type"] == "refresh"


def test_refresh_token_is_not_valid_as_access_token():
    token = create_refresh_token({"sub": "user-123"})

    try:
        verify_access_token(token)
        assert False
    except JWTError:
        assert True


def test_access_token_is_not_valid_as_refresh_token():
    token = create_access_token({"sub": "user-123"})

    try:
        verify_refresh_token(token)
        assert False
    except JWTError:
        assert True