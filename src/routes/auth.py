from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.jwt_utils import create_access_token
from src.core.security import hash_password, verify_password
from src.crud.user_crud import create_user, get_user_by_email
from src.database import get_db
from src.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from src.crypto.crypto_utils import generate_and_protect_keypair

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = get_user_by_email(db, payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese correo electrónico",
        )

    password_hash = hash_password(payload.password)

    public_key, encrypted_private_key = generate_and_protect_keypair(payload.password)

    user = create_user(
        db=db,
        email=payload.email,
        display_name=payload.display_name,
        password_hash=password_hash,
        public_key=public_key,
        encrypted_private_key=encrypted_private_key,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo crear el usuario",
        )

    return RegisterResponse(
        message="Usuario registrado exitosamente",
        user_id=str(user.id),
        email=user.email,
        display_name=user.display_name,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, payload.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
        }
    )

    return TokenResponse(access_token=access_token)