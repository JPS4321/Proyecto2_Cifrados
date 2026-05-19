# src/crypto/signatures.py

import base64
import hashlib
from typing import Union

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa, utils


def _b64encode(data: bytes) -> str:
    """
    Convierte bytes a string Base64.
    """
    return base64.b64encode(data).decode("utf-8")


def _b64decode(data: str) -> bytes:
    """
    Convierte string Base64 a bytes.
    """
    return base64.b64decode(data.encode("utf-8"))


def _load_private_key(private_key_pem: Union[str, bytes]) -> rsa.RSAPrivateKey:
    """
    Carga una llave privada RSA desde formato PEM.
    """
    if isinstance(private_key_pem, str):
        private_key_pem = private_key_pem.encode("utf-8")

    private_key = serialization.load_pem_private_key(
        private_key_pem,
        password=None
    )

    if not isinstance(private_key, rsa.RSAPrivateKey):
        raise ValueError("La llave privada debe ser RSA.")

    return private_key


def _load_public_key(public_key_pem: Union[str, bytes]) -> rsa.RSAPublicKey:
    """
    Carga una llave pública RSA desde formato PEM.
    """
    if isinstance(public_key_pem, str):
        public_key_pem = public_key_pem.encode("utf-8")

    public_key = serialization.load_pem_public_key(public_key_pem)

    if not isinstance(public_key, rsa.RSAPublicKey):
        raise ValueError("La llave pública debe ser RSA.")

    return public_key


def hash_message_sha256(plaintext: str) -> str:
    """
    Calcula el hash SHA-256 del mensaje original en texto claro.

    Retorna:
        Hash hexadecimal de 64 caracteres.
    """
    if not isinstance(plaintext, str) or plaintext == "":
        raise ValueError("El plaintext debe ser un string no vacío.")

    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


def sign_message_hash(
    private_key_pem: Union[str, bytes],
    message_hash_hex: str
) -> str:
    """
    Firma un hash SHA-256 usando RSA-PSS.

    Importante:
        Esta función firma el hash del mensaje, no el plaintext directamente.

    Recibe:
        private_key_pem: llave privada RSA en formato PEM.
        message_hash_hex: SHA-256 del plaintext en hexadecimal.

    Retorna:
        Firma digital en Base64.
    """
    if not isinstance(message_hash_hex, str) or len(message_hash_hex) != 64:
        raise ValueError("El hash del mensaje debe ser un SHA-256 hexadecimal de 64 caracteres.")

    private_key = _load_private_key(private_key_pem)
    message_hash_bytes = bytes.fromhex(message_hash_hex)

    signature = private_key.sign(
        message_hash_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        utils.Prehashed(hashes.SHA256())
    )

    return _b64encode(signature)


def verify_message_signature(
    public_key_pem: Union[str, bytes],
    message_hash_hex: str,
    signature_b64: str
) -> bool:
    """
    Verifica una firma RSA-PSS sobre un hash SHA-256.

    Recibe:
        public_key_pem: llave pública RSA del remitente.
        message_hash_hex: SHA-256 del plaintext en hexadecimal.
        signature_b64: firma digital en Base64.

    Retorna:
        True si la firma es válida.
        False si la firma es inválida.
    """
    if not isinstance(message_hash_hex, str) or len(message_hash_hex) != 64:
        raise ValueError("El hash del mensaje debe ser un SHA-256 hexadecimal de 64 caracteres.")

    public_key = _load_public_key(public_key_pem)
    message_hash_bytes = bytes.fromhex(message_hash_hex)
    signature = _b64decode(signature_b64)

    try:
        public_key.verify(
            signature,
            message_hash_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            utils.Prehashed(hashes.SHA256())
        )
        return True
    except InvalidSignature:
        return False


def sign_plaintext_message(
    private_key_pem: Union[str, bytes],
    plaintext: str
) -> dict:
    """
    Función de alto nivel para que API la pueda usar fácilmente.

    Recibe:
        private_key_pem: llave privada RSA del remitente.
        plaintext: mensaje original.

    Retorna:
        {
            "message_hash": str,
            "signature": str
        }
    """
    message_hash = hash_message_sha256(plaintext)
    signature = sign_message_hash(private_key_pem, message_hash)

    return {
        "message_hash": message_hash,
        "signature": signature
    }


def verify_plaintext_message(
    public_key_pem: Union[str, bytes],
    plaintext: str,
    signature_b64: str
) -> bool:
    """
    Función de alto nivel para verificar una firma directamente desde el plaintext.
    """
    message_hash = hash_message_sha256(plaintext)
    return verify_message_signature(
        public_key_pem=public_key_pem,
        message_hash_hex=message_hash,
        signature_b64=signature_b64
    )