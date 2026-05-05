from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.crypto.crypto_utils import decrypt_private_key
from src.crypto.message_crypto import encrypt_message_for_recipient, decrypt_message_for_recipient
from src.crud.message_crud import (
    create_message,
    create_message_key,
    get_messages_for_user,
    get_message_by_id,
    get_message_key_for_user,
)
from src.crud.user_crud import get_user_by_id
from src.database import get_db
from src.schemas.message import (
    MessageCreate,
    MessageResponse,
    MessageWithKeyResponse,
    MessageDecryptRequest,
    MessageDecryptResponse,
)

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(payload: MessageCreate, db: Session = Depends(get_db)):
    sender = get_user_by_id(db, payload.sender_id)
    if not sender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Remitente no encontrado",
        )

    recipient = get_user_by_id(db, payload.recipient_id)
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destinatario no encontrado",
        )

    encrypted_payload = encrypt_message_for_recipient(
        plaintext=payload.plaintext,
        recipient_public_key_pem=recipient.public_key,
    )

    message = create_message(
        db,
        {
            "sender_id": payload.sender_id,
            "recipient_id": payload.recipient_id,
            "group_id": None,
            "ciphertext": encrypted_payload["ciphertext"],
            "nonce": encrypted_payload["nonce"],
            "auth_tag": encrypted_payload["auth_tag"],
        },
    )

    create_message_key(
        db,
        message_id=message.id,
        user_id=payload.recipient_id,
        encrypted_key=encrypted_payload["encrypted_key"],
    )

    return message

@router.get("/{user_id}", response_model=list[MessageWithKeyResponse])
def get_user_messages(user_id: str, db: Session = Depends(get_db)):
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
):
    message = get_message_by_id(db, message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mensaje no encontrado",
        )

    user = get_user_by_id(db, str(payload.user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    message_key = get_message_key_for_user(
        db,
        message_id=message_id,
        user_id=str(payload.user_id),
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

    return MessageDecryptResponse(
        message_id=str(message.id),
        plaintext=plaintext,
    )