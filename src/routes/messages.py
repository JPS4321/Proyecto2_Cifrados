from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.blockchain.blockchain_utils import mine_block
from src.crypto.crypto_utils import decrypt_private_key
from src.crypto.message_crypto import (
    encrypt_message_for_recipient,
    decrypt_message_for_recipient,
    encrypt_message_for_group,
)
from src.crypto.signatures import (
    sign_plaintext_message,
    verify_plaintext_message,
)
from src.crud.blockchain_crud import (
    get_last_block,
    create_block,
)
from src.crud.message_crud import (
    create_message,
    create_message_key,
    get_messages_for_user,
    get_message_by_id,
    get_message_key_for_user,
    update_message_signature_status,
)
from src.crud.user_crud import get_user_by_id
from src.database import get_db
from src.dependencies import get_current_user
from src.schemas.message import (
    MessageCreate,
    MessageResponse,
    MessageWithKeyResponse,
    MessageDecryptRequest,
    MessageDecryptResponse,
    MessageVerifyRequest,
    MessageVerifyResponse,
    GroupMessageCreate,
    GroupMessageResponse,
)

router = APIRouter(prefix="/messages", tags=["messages"])


def _create_block_for_message(db: Session, message):
    """
    Crea automáticamente un bloque para un mensaje firmado.
    """
    if not message.message_hash:
        raise ValueError("El mensaje no tiene message_hash para registrar en blockchain.")

    last_block = get_last_block(db)

    if last_block:
        previous_hash = last_block.hash
        block_index = last_block.index + 1
    else:
        previous_hash = "0" * 64
        block_index = 0

    timestamp = datetime.utcnow()

    nonce, block_hash = mine_block(
        index=block_index,
        timestamp=timestamp,
        sender_id=str(message.sender_id),
        recipient_id=str(message.recipient_id) if message.recipient_id else None,
        message_hash=message.message_hash,
        previous_hash=previous_hash,
    )

    return create_block(
        db,
        {
            "index": block_index,
            "timestamp": timestamp,
            "sender_id": message.sender_id,
            "recipient_id": message.recipient_id,
            "message_hash": message.message_hash,
            "previous_hash": previous_hash,
            "nonce": nonce,
            "hash": block_hash,
        },
    )


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    payload: MessageCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Envía un mensaje cifrado a un destinatario.

    Ruta protegida con JWT.
    El remitente debe ser el mismo usuario autenticado.
    """
    if str(payload.sender_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes enviar mensajes en nombre de otro usuario.",
        )

    sender = current_user

    recipient = get_user_by_id(db, payload.recipient_id)
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destinatario no encontrado",
        )

    try:
        sender_private_key_pem = decrypt_private_key(
            sender.encrypted_private_key,
            payload.sender_password,
        )

        signature_payload = sign_plaintext_message(
            private_key_pem=sender_private_key_pem,
            plaintext=payload.plaintext,
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo firmar el mensaje. Verifica la contraseña del remitente.",
        )

    encrypted_payload = encrypt_message_for_recipient(
        plaintext=payload.plaintext,
        recipient_public_key_pem=recipient.public_key,
    )

    message = create_message(
        db,
        {
            "sender_id": sender.id,
            "recipient_id": payload.recipient_id,
            "group_id": None,
            "ciphertext": encrypted_payload["ciphertext"],
            "nonce": encrypted_payload["nonce"],
            "auth_tag": encrypted_payload["auth_tag"],
            "signature": signature_payload["signature"],
            "signature_valid": None,
            "message_hash": signature_payload["message_hash"],
        },
    )

    create_message_key(
        db,
        message_id=message.id,
        user_id=payload.recipient_id,
        encrypted_key=encrypted_payload["encrypted_key"],
    )

    try:
        _create_block_for_message(db, message)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="El mensaje fue creado, pero no se pudo registrar en blockchain.",
        )

    return message


@router.get("/{user_id}", response_model=list[MessageWithKeyResponse])
def get_user_messages(
    user_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Obtiene los mensajes de un usuario.

    Ruta protegida con JWT.
    Un usuario solo puede consultar sus propios mensajes.
    """
    if str(user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes consultar mensajes de otro usuario.",
        )

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    results = get_messages_for_user(db, user_id)

    messages = []
    for message, message_key in results:
        messages.append(
            MessageWithKeyResponse(
                id=message.id,
                sender_id=message.sender_id,
                recipient_id=message.recipient_id,
                group_id=message.group_id,
                ciphertext=message.ciphertext,
                nonce=message.nonce,
                auth_tag=message.auth_tag,
                signature=message.signature,
                signature_valid=message.signature_valid,
                message_hash=message.message_hash,
                created_at=message.created_at,
                encrypted_key=message_key.encrypted_key,
            )
        )

    return messages


@router.post("/{message_id}/decrypt", response_model=MessageDecryptResponse)
def decrypt_message(
    message_id: str,
    payload: MessageDecryptRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Descifra un mensaje.

    Ruta protegida con JWT.
    El usuario del payload debe coincidir con el usuario autenticado.
    """
    if str(payload.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes descifrar mensajes de otro usuario.",
        )

    message = get_message_by_id(db, message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mensaje no encontrado",
        )

    user = current_user

    sender = get_user_by_id(db, str(message.sender_id))
    if not sender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Remitente no encontrado",
        )

    message_key = get_message_key_for_user(
        db,
        message_id=message_id,
        user_id=str(user.id),
    )

    if not message_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no tiene permiso para descifrar este mensaje",
        )

    try:
        private_key_pem = decrypt_private_key(
            user.encrypted_private_key,
            payload.password,
        )

        plaintext = decrypt_message_for_recipient(
            ciphertext=message.ciphertext,
            encrypted_key=message_key.encrypted_key,
            nonce=message.nonce,
            auth_tag=message.auth_tag,
            recipient_private_key_pem=private_key_pem,
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo descifrar el mensaje. Verifica la contraseña o los datos cifrados.",
        )

    signature_valid = False
    warning = None

    if not message.signature:
        warning = "El mensaje no tiene firma digital registrada."
    else:
        try:
            signature_valid = verify_plaintext_message(
                public_key_pem=sender.public_key,
                plaintext=plaintext,
                signature_b64=message.signature,
            )

            update_message_signature_status(
                db,
                message_id=message.id,
                signature_valid=signature_valid,
            )

            if not signature_valid:
                warning = "Firma inválida: el mensaje no pudo ser verificado."

        except Exception:
            warning = "No se pudo verificar la firma del mensaje."

    return MessageDecryptResponse(
        message_id=str(message.id),
        plaintext=plaintext,
        signature_valid=signature_valid,
        warning=warning,
    )


@router.post("/{message_id}/verify", response_model=MessageVerifyResponse)
def verify_message(
    message_id: str,
    payload: MessageVerifyRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Verifica la firma digital de un mensaje.

    Ruta protegida con JWT.
    El usuario del payload debe coincidir con el usuario autenticado.
    """
    if str(payload.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes verificar mensajes de otro usuario.",
        )

    message = get_message_by_id(db, message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mensaje no encontrado",
        )

    user = current_user

    sender = get_user_by_id(db, str(message.sender_id))
    if not sender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Remitente no encontrado",
        )

    message_key = get_message_key_for_user(
        db,
        message_id=message_id,
        user_id=str(user.id),
    )

    if not message_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no tiene permiso para verificar este mensaje",
        )

    if not message.signature:
        update_message_signature_status(
            db,
            message_id=message.id,
            signature_valid=False,
        )

        return MessageVerifyResponse(
            message_id=str(message.id),
            signature_valid=False,
            warning="El mensaje no tiene firma digital registrada.",
        )

    try:
        private_key_pem = decrypt_private_key(
            user.encrypted_private_key,
            payload.password,
        )

        plaintext = decrypt_message_for_recipient(
            ciphertext=message.ciphertext,
            encrypted_key=message_key.encrypted_key,
            nonce=message.nonce,
            auth_tag=message.auth_tag,
            recipient_private_key_pem=private_key_pem,
        )

        signature_valid = verify_plaintext_message(
            public_key_pem=sender.public_key,
            plaintext=plaintext,
            signature_b64=message.signature,
        )

        update_message_signature_status(
            db,
            message_id=message.id,
            signature_valid=signature_valid,
        )

    except Exception:
        update_message_signature_status(
            db,
            message_id=message.id,
            signature_valid=False,
        )

        return MessageVerifyResponse(
            message_id=str(message.id),
            signature_valid=False,
            warning="No se pudo verificar la firma. Verifica la contraseña o los permisos del usuario.",
        )

    return MessageVerifyResponse(
        message_id=str(message.id),
        signature_valid=signature_valid,
        warning=None if signature_valid else "Firma inválida: el mensaje no pudo ser verificado.",
    )


@router.post("/group", response_model=GroupMessageResponse, status_code=status.HTTP_201_CREATED)
def send_group_message(
    payload: GroupMessageCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Envía un mensaje grupal cifrado.

    Ruta protegida con JWT.
    El remitente debe ser el mismo usuario autenticado.
    """
    if str(payload.sender_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes enviar mensajes grupales en nombre de otro usuario.",
        )

    sender = current_user

    if not payload.recipient_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe incluir al menos un destinatario",
        )

    try:
        sender_private_key_pem = decrypt_private_key(
            sender.encrypted_private_key,
            payload.sender_password,
        )

        signature_payload = sign_plaintext_message(
            private_key_pem=sender_private_key_pem,
            plaintext=payload.plaintext,
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo firmar el mensaje grupal. Verifica la contraseña del remitente.",
        )

    recipients_public_keys = {}

    for recipient_id in payload.recipient_ids:
        recipient = get_user_by_id(db, recipient_id)
        if not recipient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Destinatario no encontrado: {recipient_id}",
            )

        recipients_public_keys[recipient_id] = recipient.public_key

    encrypted_payload = encrypt_message_for_group(
        plaintext=payload.plaintext,
        recipients_public_keys=recipients_public_keys,
    )

    message = create_message(
        db,
        {
            "sender_id": sender.id,
            "recipient_id": None,
            "group_id": payload.group_id,
            "ciphertext": encrypted_payload["ciphertext"],
            "nonce": encrypted_payload["nonce"],
            "auth_tag": encrypted_payload["auth_tag"],
            "signature": signature_payload["signature"],
            "signature_valid": None,
            "message_hash": signature_payload["message_hash"],
        },
    )

    encrypted_keys_count = 0

    for key_data in encrypted_payload["encrypted_keys"]:
        create_message_key(
            db,
            message_id=message.id,
            user_id=key_data["user_id"],
            encrypted_key=key_data["encrypted_key"],
        )
        encrypted_keys_count += 1

    try:
        _create_block_for_message(db, message)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="El mensaje grupal fue creado, pero no se pudo registrar en blockchain.",
        )

    return GroupMessageResponse(
        id=str(message.id),
        sender_id=str(message.sender_id),
        recipient_id=None,
        group_id=str(message.group_id),
        ciphertext=message.ciphertext,
        nonce=message.nonce,
        auth_tag=message.auth_tag,
        signature=message.signature,
        signature_valid=message.signature_valid,
        message_hash=message.message_hash,
        encrypted_keys_count=encrypted_keys_count,
        created_at=message.created_at,
    )