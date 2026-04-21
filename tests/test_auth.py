from src.core.jwt_utils import create_access_token, verify_token
from src.core.security import hash_password, verify_password

def test_hash_and_verify_password():
    password = "PasswordSegura2026"
    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash) is True
    assert verify_password("clave_incorrecta", password_hash) is False

def test_create_and_verify_jwt():
    token = create_access_token({"sub": "jpezko2026", "email": "jpezko@example.com"})
    payload = verify_token(token)

    assert payload["sub"] == "jpezko2026"
    assert payload["email"] == "jpezko@example.com"
    assert "exp" in payload