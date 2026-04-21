import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta

SECRET_KEY = "SECRET_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

class JWTError(Exception):
    pass

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    header = {"alg": ALGORITHM, "typ": "JWT"}
    payload = data.copy()

    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload["exp"] = int(expire.timestamp())

    header_b64 = _b64url_encode(
        json.dumps(header, separators=(",", ":")).encode("utf-8")
    )
    payload_b64 = _b64url_encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    )

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()

    signature_b64 = _b64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def verify_token(token: str) -> dict:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError as exc:
        raise JWTError("Token inválido") from exc

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    expected_signature_b64 = _b64url_encode(expected_signature)

    if not hmac.compare_digest(signature_b64, expected_signature_b64):
        raise JWTError("Firma inválida")

    payload = json.loads(_b64url_decode(payload_b64))
    exp = payload.get("exp")

    if exp is None:
        raise JWTError("Token sin expiración")

    if int(datetime.now(UTC).timestamp()) > int(exp):
        raise JWTError("Token expirado")

    return payload