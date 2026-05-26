from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.core.jwt_utils import JWTError, verify_access_token
from src.crud.user_crud import get_user_by_id
from src.database import get_db

# Esquema HTTP Bearer para leer tokens tipo
# Authorization: Bearer <token>
bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    """
    Obtiene el usuario autenticado a partir del access token.

    Flujo:
    1. Lee el token enviado en el header Authorization
    2. Verifica que el token sea válido
    3. Extrae el user_id del campo 'sub'
    4. Busca ese usuario en la base de datos
    5. Retorna el usuario autenticado
    """

    token = credentials.credentials

    # Verifica firma, expiración y tipo del access token
    try:
        payload = verify_access_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )

    # El campo 'sub' identifica al usuario autenticado
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token no contiene un usuario válido",
        )

    # Busca el usuario real en la base de datos
    user = get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario autenticado no existe",
        )

    return user