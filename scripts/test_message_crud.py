import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database import SessionLocal
from src.crud.user_crud import get_all_users
from src.crud.message_crud import (
    create_message,
    create_message_key,
    get_message_by_id,
    get_message_key_for_user,
    get_messages_for_user,
)


db = SessionLocal()

try:
    users = get_all_users(db)

    if len(users) < 2:
        print("Necesitas al menos 2 usuarios en la tabla usuarios.")
        print("Crea usuarios con POST /auth/register antes de probar mensajes.")
        exit()

    sender = users[0]
    recipient = users[1]

    message = create_message(db, {
        "sender_id": sender.id,
        "recipient_id": recipient.id,
        "group_id": None,
        "ciphertext": "ciphertext_prueba_base64",
        "nonce": "nonce_prueba_base64",
        "auth_tag": "auth_tag_prueba_base64",
    })

    print("Mensaje creado:")
    print(message.id)

    key = create_message_key(
        db=db,
        message_id=message.id,
        user_id=recipient.id,
        encrypted_key="encrypted_key_prueba_base64"
    )

    print("Message key creada:")
    print(key.id)

    found_message = get_message_by_id(db, message.id)
    print("Mensaje encontrado:")
    print(found_message.id)

    found_key = get_message_key_for_user(db, message.id, recipient.id)
    print("Key encontrada:")
    print(found_key.encrypted_key)

    user_messages = get_messages_for_user(db, recipient.id)
    print("Mensajes para recipient:")
    print(len(user_messages))

finally:
    db.close()