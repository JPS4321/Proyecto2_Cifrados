# src/schemas/auth.py

from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    """
    Datos requeridos para registrar un usuario
    """
    display_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class RegisterResponse(BaseModel):
    """
    Respuesta devuelta después de registrar un usuario
    """
    message: str
    user_id: str
    email: EmailStr
    display_name: str

class LoginRequest(BaseModel):
    """
    Datos para login

    totp_code es opcional porque:
    - si MFA no está activo, no se necesita
    - si MFA está activo, se exige después de validar password
    """
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    totp_code: str | None = None


class LoginResponse(BaseModel):
    """
    Respuesta flexible para login

    Puede devolver:
    - tokens si el login se completa
    - mfa_required=True si falta código TOTP
    """
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str | None = "bearer"
    mfa_required: bool = False
    message: str | None = None


class TokenResponse(BaseModel):
    """
    Respuesta cuando el sistema emite tokens completos.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """
    Request para pedir un nuevo access token usando refresh token
    """
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """
    Respuesta del endpoint /auth/refresh
    Solo devuelve un nuevo access token
    """
    access_token: str
    token_type: str = "bearer"


class MFAEnableResponse(BaseModel):
    """
    Respuesta al activar MFA

    Para la demo se devuelve el secreto y la URL otpauth,
    compatible con Google Authenticator o apps similares
    """
    message: str
    totp_secret: str
    otpauth_url: str


class MFAVerifyRequest(BaseModel):
    """
    Código TOTP de 6 dígitos que genera la app autenticadora
    """
    code: str = Field(..., min_length=6, max_length=6)


class MFAVerifyResponse(BaseModel):
    """
    Respuesta al verificar manualmente un código MFA
    """
    mfa_valid: bool
    message: str