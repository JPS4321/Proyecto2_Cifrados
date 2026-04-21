# src/core/crypto_utils.py

import os
import json
import base64
from typing import Tuple, Dict, Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# =========================
# Configuración recomendada
# =========================
RSA_KEY_SIZE = 2048
PUBLIC_EXPONENT = 65537
AES_KEY_SIZE = 32           # 32 bytes = AES-256
PBKDF2_ITERATIONS = 390000
SALT_SIZE = 16
NONCE_SIZE = 12


# =========================
# Helpers Base64
# =========================
def _b64encode(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


def _b64decode(data: str) -> bytes:
    return base64.b64decode(data.encode("utf-8"))


# =========================
# Generación de llaves RSA
# =========================
def generate_rsa_keypair() -> Tuple[str, str]:
    """
    Genera un par de llaves RSA-2048 y devuelve:
    - private_key_pem (str)
    - public_key_pem (str)
    """
    private_key = rsa.generate_private_key(
        public_exponent=PUBLIC_EXPONENT,
        key_size=RSA_KEY_SIZE
    )

    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode("utf-8")

    public_key_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode("utf-8")

    return private_key_pem, public_key_pem


# =========================
# Derivación de clave
# =========================
def derive_key_from_password(password: str, salt: bytes) -> bytes:
    """
    Deriva una clave de 32 bytes a partir de la contraseña del usuario
    usando PBKDF2-HMAC-SHA256.
    """
    if not isinstance(password, str) or not password:
        raise ValueError("La contraseña debe ser un string no vacío.")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=AES_KEY_SIZE,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )

    return kdf.derive(password.encode("utf-8"))


# =========================
# Cifrado de llave privada
# =========================
def encrypt_private_key(private_key_pem: str, password: str) -> str:
    """
    Cifra la llave privada PEM usando:
    - clave derivada con PBKDF2
    - AES-256-GCM

    Retorna un JSON serializado (str) con:
    {
      "kdf": "PBKDF2-HMAC-SHA256",
      "iterations": ...,
      "salt": "...",
      "nonce": "...",
      "ciphertext": "..."
    }
    """
    if not isinstance(private_key_pem, str) or not private_key_pem.strip():
        raise ValueError("La llave privada PEM debe ser un string no vacío.")

    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    derived_key = derive_key_from_password(password, salt)

    aesgcm = AESGCM(derived_key)
    ciphertext = aesgcm.encrypt(
        nonce=nonce,
        data=private_key_pem.encode("utf-8"),
        associated_data=None
    )

    encrypted_payload = {
        "kdf": "PBKDF2-HMAC-SHA256",
        "iterations": PBKDF2_ITERATIONS,
        "salt": _b64encode(salt),
        "nonce": _b64encode(nonce),
        "ciphertext": _b64encode(ciphertext),
    }

    return json.dumps(encrypted_payload)


# =========================
# Descifrado de llave privada
# =========================
def decrypt_private_key(encrypted_private_key_json: str, password: str) -> str:
    """
    Descifra una llave privada previamente cifrada por encrypt_private_key().
    Devuelve la llave privada PEM original.
    """
    if not isinstance(encrypted_private_key_json, str) or not encrypted_private_key_json.strip():
        raise ValueError("El contenido cifrado debe ser un string JSON no vacío.")

    payload: Dict[str, Any] = json.loads(encrypted_private_key_json)

    required_fields = {"kdf", "iterations", "salt", "nonce", "ciphertext"}
    missing_fields = required_fields - payload.keys()
    if missing_fields:
        raise ValueError(f"Faltan campos requeridos en el JSON cifrado: {missing_fields}")

    salt = _b64decode(payload["salt"])
    nonce = _b64decode(payload["nonce"])
    ciphertext = _b64decode(payload["ciphertext"])

    derived_key = derive_key_from_password(password, salt)

    aesgcm = AESGCM(derived_key)
    plaintext = aesgcm.decrypt(
        nonce=nonce,
        data=ciphertext,
        associated_data=None
    )

    return plaintext.decode("utf-8")


# =========================
# Función de alto nivel
# =========================
def generate_and_protect_keypair(password: str) -> Tuple[str, str]:
    """
    Genera un par de llaves RSA-2048 y protege la llave privada usando
    una clave derivada de la contraseña del usuario mediante PBKDF2
    y cifrado AES-256-GCM.

    USO (para el endpoint de registro):
        public_key, encrypted_private_key = generate_and_protect_keypair(password)

    RETORNA:
        - public_key (str): Llave pública en formato PEM
        - encrypted_private_key (str): JSON serializado con:
            {
              "kdf": "PBKDF2-HMAC-SHA256",
              "iterations": ...,
              "salt": "...",
              "nonce": "...",
              "ciphertext": "..."
            }

    IMPORTANTE:
        - `public_key` se guarda en la columna `public_key`
        - `encrypted_private_key` se guarda directamente como TEXT en la DB
        - El tag de autenticación de AES-GCM está incluido dentro de `ciphertext`

    """
    private_key_pem, public_key_pem = generate_rsa_keypair()
    encrypted_private_key_json = encrypt_private_key(private_key_pem, password)
    return public_key_pem, encrypted_private_key_json