# src/crypto/message_crypto.py

import os
import base64
from typing import Dict, List, Union

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


AES_KEY_SIZE = 32      # 32 bytes = AES-256
GCM_NONCE_SIZE = 12
GCM_TAG_SIZE = 16      # Tag de autenticación GCM = 16 bytes


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


def _load_public_key(public_key_pem: Union[str, bytes]):
    """
    Carga una llave pública RSA en formato PEM.
    """
    if isinstance(public_key_pem, str):
        public_key_pem = public_key_pem.encode("utf-8")

    public_key = serialization.load_pem_public_key(public_key_pem)

    if not isinstance(public_key, rsa.RSAPublicKey):
        raise ValueError("La llave pública debe ser RSA.")

    return public_key


def _load_private_key(private_key_pem: Union[str, bytes]):
    """
    Carga una llave privada RSA en formato PEM.
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


def generate_aes_key() -> bytes:
    """
    Genera una clave AES-256 efímera de 32 bytes.

    Esta clave debe generarse una vez por mensaje.
    """
    return os.urandom(AES_KEY_SIZE)


def encrypt_aes_gcm(plaintext: str, aes_key: bytes) -> Dict[str, str]:
    """
    Cifra un mensaje usando AES-256-GCM.

    Recibe:
        plaintext: mensaje original en texto claro.
        aes_key: clave AES de 32 bytes.

    Retorna:
        {
            "ciphertext": "...base64...",
            "nonce": "...base64...",
            "auth_tag": "...base64..."
        }

    Notes:
        - El nonce se genera nuevo para cada cifrado.
        - El plaintext nunca debe guardarse en base de datos.
        - cryptography AESGCM devuelve ciphertext + tag juntos.
          Por eso se separan los últimos 16 bytes como auth_tag.
    """
    
    if not isinstance(plaintext, str) or plaintext == "":
        raise ValueError("El plaintext debe ser un string no vacío.")

    if not isinstance(aes_key, bytes) or len(aes_key) != AES_KEY_SIZE:
        raise ValueError("La clave AES debe tener exactamente 32 bytes.")

    nonce = os.urandom(GCM_NONCE_SIZE)
    aesgcm = AESGCM(aes_key)

    encrypted_data = aesgcm.encrypt(
        nonce=nonce,
        data=plaintext.encode("utf-8"),
        associated_data=None
    )

    ciphertext = encrypted_data[:-GCM_TAG_SIZE]
    auth_tag = encrypted_data[-GCM_TAG_SIZE:]

    return {
        "ciphertext": _b64encode(ciphertext),
        "nonce": _b64encode(nonce),
        "auth_tag": _b64encode(auth_tag),
    }


def decrypt_aes_gcm(
    ciphertext_b64: str,
    nonce_b64: str,
    tag_b64: str,
    aes_key: bytes
) -> str:
    """
    Descifra un mensaje cifrado con AES-256-GCM.

    Recibe:
        ciphertext_b64: ciphertext en Base64.
        nonce_b64: nonce en Base64.
        tag_b64: auth_tag en Base64.
        aes_key: clave AES de 32 bytes.

    Retorna:
        plaintext original.
    """
    if not isinstance(aes_key, bytes) or len(aes_key) != AES_KEY_SIZE:
        raise ValueError("La clave AES debe tener exactamente 32 bytes.")

    ciphertext = _b64decode(ciphertext_b64)
    nonce = _b64decode(nonce_b64)
    auth_tag = _b64decode(tag_b64)

    encrypted_data = ciphertext + auth_tag

    aesgcm = AESGCM(aes_key)
    plaintext = aesgcm.decrypt(
        nonce=nonce,
        data=encrypted_data,
        associated_data=None
    )

    return plaintext.decode("utf-8")


def encrypt_aes_key_with_public_key(
    aes_key: bytes,
    public_key_pem: Union[str, bytes]
) -> str:
    """
    Cifra una clave AES usando RSA-OAEP con la llave pública del destinatario.

    Recibe:
        aes_key: clave AES de 32 bytes.
        public_key_pem: llave pública RSA en formato PEM.

    Retorna:
        encrypted_key en Base64.
    """
    if not isinstance(aes_key, bytes) or len(aes_key) != AES_KEY_SIZE:
        raise ValueError("La clave AES debe tener exactamente 32 bytes.")

    public_key = _load_public_key(public_key_pem)

    encrypted_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    return _b64encode(encrypted_key)


def decrypt_aes_key_with_private_key(
    encrypted_key_b64: str,
    private_key_pem: Union[str, bytes]
) -> bytes:
    """
    Descifra una clave AES usando RSA-OAEP con la llave privada del destinatario.

    Recibe:
        encrypted_key_b64: clave AES cifrada en Base64.
        private_key_pem: llave privada RSA en formato PEM.

    Retorna:
        aes_key original en bytes.
    """
    private_key = _load_private_key(private_key_pem)
    encrypted_key = _b64decode(encrypted_key_b64)

    aes_key = private_key.decrypt(
        encrypted_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    if len(aes_key) != AES_KEY_SIZE:
        raise ValueError("La clave AES descifrada no tiene 32 bytes.")

    return aes_key


def encrypt_message_for_recipient(
    plaintext: str,
    recipient_public_key_pem: Union[str, bytes]
) -> Dict[str, str]:
    """
    Flujo híbrido para mensaje individual.

    Pasos:
        1. Genera una clave AES-256 efímera.
        2. Cifra el plaintext con AES-256-GCM.
        3. Cifra la clave AES con RSA-OAEP usando la llave pública del destinatario.
        4. Devuelve todo en Base64.

    Retorna:
        {
            "ciphertext": str,
            "encrypted_key": str,
            "nonce": str,
            "auth_tag": str
        }
    """
    aes_key = generate_aes_key()

    encrypted_message = encrypt_aes_gcm(
        plaintext=plaintext,
        aes_key=aes_key
    )

    encrypted_key = encrypt_aes_key_with_public_key(
        aes_key=aes_key,
        public_key_pem=recipient_public_key_pem
    )

    return {
        "ciphertext": encrypted_message["ciphertext"],
        "encrypted_key": encrypted_key,
        "nonce": encrypted_message["nonce"],
        "auth_tag": encrypted_message["auth_tag"],
    }


def decrypt_message_for_recipient(
    ciphertext: str,
    encrypted_key: str,
    nonce: str,
    auth_tag: str,
    recipient_private_key_pem: Union[str, bytes]
) -> str:
    """
    Descifra un mensaje individual o grupal para un destinatario específico.

    Pasos:
        1. Descifra encrypted_key con RSA-OAEP usando la llave privada del destinatario.
        2. Recupera la clave AES.
        3. Descifra ciphertext con AES-256-GCM.
        4. Retorna plaintext.
    """
    aes_key = decrypt_aes_key_with_private_key(
        encrypted_key_b64=encrypted_key,
        private_key_pem=recipient_private_key_pem
    )

    plaintext = decrypt_aes_gcm(
        ciphertext_b64=ciphertext,
        nonce_b64=nonce,
        tag_b64=auth_tag,
        aes_key=aes_key
    )

    return plaintext


def encrypt_message_for_group(
    plaintext: str,
    recipients_public_keys: Dict[str, Union[str, bytes]]
) -> Dict[str, object]:
    """
    Flujo híbrido para mensajes grupales

    Recibe:
        plaintext: mensaje original.
        recipients_public_keys:
            {
                "user_id_1": "-----BEGIN PUBLIC KEY-----...",
                "user_id_2": "-----BEGIN PUBLIC KEY-----..."
            }

    Pasos:
        1. Genera una sola clave AES-256.
        2. Cifra el mensaje una sola vez con AES-256-GCM.
        3. Cifra esa misma clave AES con la llave pública de cada destinatario.
        4. Devuelve una lista encrypted_keys, una por usuario.

    Retorna:
        {
            "ciphertext": str,
            "nonce": str,
            "auth_tag": str,
            "encrypted_keys": [
                {
                    "user_id": str,
                    "encrypted_key": str
                }
            ]
        }
    """
    if not recipients_public_keys:
        raise ValueError("Debe existir al menos un destinatario para el mensaje grupal.")

    aes_key = generate_aes_key()

    encrypted_message = encrypt_aes_gcm(
        plaintext=plaintext,
        aes_key=aes_key
    )

    encrypted_keys: List[Dict[str, str]] = []

    for user_id, public_key_pem in recipients_public_keys.items():
        encrypted_key = encrypt_aes_key_with_public_key(
            aes_key=aes_key,
            public_key_pem=public_key_pem
        )

        encrypted_keys.append({
            "user_id": str(user_id),
            "encrypted_key": encrypted_key
        })

    return {
        "ciphertext": encrypted_message["ciphertext"],
        "nonce": encrypted_message["nonce"],
        "auth_tag": encrypted_message["auth_tag"],
        "encrypted_keys": encrypted_keys,
    }