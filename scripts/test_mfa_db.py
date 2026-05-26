from src.database import SessionLocal

from src.crud.user_crud import (
    get_user_by_email,
    update_user_totp_secret
)


db = SessionLocal()

try:
    user = get_user_by_email(
        db,
        "KOU@example.com"
    )

    if not user:
        print("Usuario no encontrado")
        exit()

    updated_user = update_user_totp_secret(
        db=db,
        user_id=user.id,
        totp_secret="JBSWY3DPEHPK3PXP"
    )

    print("TOTP actualizado correctamente:")
    print(updated_user.email)
    print(updated_user.totp_secret)

finally:
    db.close()