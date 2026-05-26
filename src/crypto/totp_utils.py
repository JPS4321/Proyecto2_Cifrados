# src/crypto/totp_utils.py

import pyotp


ISSUER_NAME = "VaultChain"


def generate_totp_secret() -> str:
    """
    Genera un secreto Base32 para TOTP.
    Este secreto se guarda en users.totp_secret.
    """
    return pyotp.random_base32()


def build_totp_uri(email: str, secret: str) -> str:
    """
    Genera la URL otpauth:// que puede usarse para crear un QR
    o configurarse en una app como Google Authenticator.
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(
        name=email,
        issuer_name=ISSUER_NAME,
    )


def verify_totp_code(secret: str, code: str) -> bool:
    """
    Verifica un código TOTP de 6 dígitos.

    valid_window=1 permite una pequeña tolerancia de tiempo:
    acepta el intervalo actual, uno anterior o uno posterior.
    """
    if not secret or not code:
        return False

    code = code.strip()

    if not code.isdigit() or len(code) != 6:
        return False

    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)