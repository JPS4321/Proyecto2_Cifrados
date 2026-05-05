from sqlalchemy.orm import Session

from src.models.message import Message
from src.models.message_key import MessageKey

#Crear nuevo mensaje cifrado
def create_message(db: Session, message_data: dict):
    message = Message(**message_data)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

#Almacena la clave simétrica del mensaje cifrada para un usuario específico.
def create_message_key(db: Session, message_id, user_id, encrypted_key):
    key = MessageKey(
        message_id=message_id,
        user_id=user_id,
        encrypted_key=encrypted_key
    )
    db.add(key)
    db.commit()
    return key


#Obtiene un mensaje por su ID.
def get_message_by_id(db: Session, message_id):
    return db.query(Message).filter(Message.id == message_id).first()


#Obtiene la clave cifrada para un mensaje y usuario específicos.
def get_message_key_for_user(db: Session, message_id, user_id):
    return db.query(MessageKey).filter(
        MessageKey.message_id == message_id,
        MessageKey.user_id == user_id
    ).first()


#  Obtiene todos los mensajes accesibles por un usuario.
def get_messages_for_user(db: Session, user_id):
    return (
        db.query(Message, MessageKey)
        .join(MessageKey, Message.id == MessageKey.message_id)
        .filter(MessageKey.user_id == user_id)
        .all()
    )