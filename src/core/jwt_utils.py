# src/core/jwt_utils.py

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta

SECRET_KEY = "SECRET_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

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
    payload.setdefault("type", "access")

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

def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Crea un refresh token JWT.

    El refresh token se usa para solicitar un nuevo access token
    sin que el usuario tenga que volver a iniciar sesión.

    Args:
        data: Información que se incluirá dentro del token, por ejemplo:
              {"sub": user_id, "email": user_email}
        expires_delta: Tiempo de expiración personalizado. Si no se envía,
                       se usa REFRESH_TOKEN_EXPIRE_DAYS.

    Returns:
        str: Refresh token firmado en formato JWT.
    """
    payload = data.copy()

    # Marcamos explícitamente el tipo de token para diferenciarlo
    # de un access token normal.
    payload["type"] = "refresh"

    # Reutilizamos la función general de creación de JWT,
    # pero con una expiración más larga.
    return create_access_token(
        payload,
        expires_delta=expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )


def verify_access_token(token: str) -> dict:
    """
    Verifica que un token JWT sea válido y que además sea un access token.

    Un access token es el token que se usa para acceder a endpoints protegidos.

    Args:
        token: Token JWT recibido desde el cliente.

    Returns:
        dict: Payload decodificado del token si es válido.

    Raises:
        JWTError: Si el token es inválido, expiró o no es de tipo access.
    """
    payload = verify_token(token)

    # Evita que un refresh token pueda usarse para acceder directamente
    # a endpoints protegidos.
    if payload.get("type") != "access":
        raise JWTError("El token no es de acceso")

    return payload


def verify_refresh_token(token: str) -> dict:
    """
    Verifica que un token JWT sea válido y que además sea un refresh token.

    Un refresh token solo debe usarse para renovar un access token,
    no para acceder directamente a endpoints protegidos.

    Args:
        token: Refresh token recibido desde el cliente.

    Returns:
        dict: Payload decodificado del token si es válido.

    Raises:
        JWTError: Si el token es inválido, expiró o no es de tipo refresh.
    """
    payload = verify_token(token)

    # Evita que un access token se use por error en el endpoint de refresh.
    if payload.get("type") != "refresh":
        raise JWTError("El token no es de refresco")

    return payload