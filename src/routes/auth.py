from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.jwt_utils import (
    JWTError,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from src.core.security import hash_password, verify_password
from src.crypto.crypto_utils import generate_and_protect_keypair
from src.crypto.totp_utils import (
    build_totp_uri,
    generate_totp_secret,
    verify_totp_code,
)
from src.crud.user_crud import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_user_totp_secret,
)
from src.database import get_db
from src.dependencies import get_current_user
from src.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    MFAEnableResponse,
    MFAVerifyRequest,
    MFAVerifyResponse,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])

def _build_token_payload(user) -> dict:
    """
    Construye el contenido que irá dentro del JWT

    'sub' es el identificador principal del usuario autenticado
    """
    return {
        "sub": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
    }


def _issue_tokens(user) -> TokenResponse:
    """
    Genera access token y refresh token para un usuario

    El access token se usa para acceder a endpoints protegidos
    El refresh token se usa para pedir un nuevo access token
    """
    token_payload = _build_token_payload(user)

    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Registra un usuario nuevo

    Flujo:
    1. Valida que el email no exista
    2. Hashea la contraseña
    3. Genera par de llaves RSA
    4. Cifra la llave privada con la contraseña del usuario
    5. Guarda el usuario en base de datos
    """
    existing_user = get_user_by_email(db, payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese correo electrónico",
        )

    # La contraseña nunca se guarda en texto plano.
    password_hash = hash_password(payload.password)

    # Genera llave pública y llave privada protegida.
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


@router.post("/login", response_model=LoginResponse, response_model_exclude_none=True)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Inicia sesión con soporte MFA

    Flujo:
    1. Verifica email y contraseña
    2. Si MFA no está activo, emite access token y refresh token
    3. Si MFA está activo y no viene totp_code, pide MFA
    4. Si MFA está activo y el código es correcto, emite tokens
    """
    user = get_user_by_email(db, payload.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    # Primero se valida password. MFA nunca se evalúa si password es incorrecta
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    # Contrato del proyecto:
    # MFA activo significa que user.totp_secret no es null
    if user.totp_secret:
        # Si tiene MFA y no mandó código, se avisa que falta el segundo factor
        if not payload.totp_code:
            return LoginResponse(
                mfa_required=True,
                message="MFA requerido para completar el inicio de sesión",
            )

        # Si mandó código, se valida contra el secreto TOTP guardado
        if not verify_totp_code(user.totp_secret, payload.totp_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Código TOTP inválido",
            )

    # Si no tiene MFA, o si MFA fue validado, se emiten tokens
    tokens = _issue_tokens(user)

    return LoginResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        mfa_required=False,
        message="Login exitoso",
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh_access_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """
    Genera un nuevo access token a partir de un refresh token válido

    Esto permite renovar sesión sin volver a ingresar usuario/password
    """
    try:
        token_payload = verify_refresh_token(payload.refresh_token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado",
        )

    user_id = token_payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token sin usuario válido",
        )

    user = get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )

    access_token = create_access_token(_build_token_payload(user))

    return RefreshTokenResponse(
        access_token=access_token,
        token_type="bearer",
    )


@router.post("/mfa/enable", response_model=MFAEnableResponse)
def enable_mfa(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Activa MFA para el usuario autenticado

    Requiere access token
    Genera un secreto TOTP y lo guarda en users.totp_secret
    """
    if current_user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="MFA ya está activo para este usuario",
        )

    # Secreto compatible con Google Authenticator.
    secret = generate_totp_secret()

    # Guardamos el secreto en la base.
    # Desde este momento MFA se considera activo.
    updated_user = update_user_totp_secret(
        db=db,
        user_id=current_user.id,
        totp_secret=secret,
    )

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo activar MFA",
        )

    # URL compatible con apps autenticadoras.
    otpauth_url = build_totp_uri(
        email=updated_user.email,
        secret=secret,
    )

    return MFAEnableResponse(
        message="MFA activado correctamente",
        totp_secret=secret,
        otpauth_url=otpauth_url,
    )


@router.post("/mfa/verify", response_model=MFAVerifyResponse)
def verify_mfa(
    payload: MFAVerifyRequest,
    current_user=Depends(get_current_user),
):
    """
    Verifica manualmente un código TOTP del usuario autenticado

    Sirve para demostrar desde Swagger que MFA quedó configurado bien
    """
    if not current_user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA no está activo para este usuario",
        )

    # Se valida el código generado por Google Authenticator o equivalente
    is_valid = verify_totp_code(
        secret=current_user.totp_secret,
        code=payload.code,
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código TOTP inválido",
        )

    return MFAVerifyResponse(
        mfa_valid=True,
        message="Código TOTP válido",
    )