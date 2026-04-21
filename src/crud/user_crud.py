from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.models.user import User

def create_user(
    db: Session,
    email: str,
    display_name: str,
    password_hash: str,
    public_key: str,
    encrypted_private_key: str,
    totp_secret: str | None = None
):
    user = User(
        email=email,
        display_name=display_name,
        password_hash=password_hash,
        public_key=public_key,
        encrypted_private_key=encrypted_private_key,
        totp_secret=totp_secret
    )

    db.add(user)

    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        return None


def get_user_by_id(db: Session, user_id):
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_all_users(db: Session):
    return db.query(User).all()


def update_user(
    db: Session,
    user_id,
    display_name: str | None = None,
    password_hash: str | None = None,
    public_key: str | None = None,
    encrypted_private_key: str | None = None,
    totp_secret: str | None = None
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return None

    if display_name is not None:
        user.display_name = display_name
    if password_hash is not None:
        user.password_hash = password_hash
    if public_key is not None:
        user.public_key = public_key
    if encrypted_private_key is not None:
        user.encrypted_private_key = encrypted_private_key
    if totp_secret is not None:
        user.totp_secret = totp_secret

    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return False

    db.delete(user)
    db.commit()
    return True