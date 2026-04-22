from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.crud.user_crud import get_user_by_id
from src.database import get_db
from src.schemas.user import PublicKeyResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}/key", response_model=PublicKeyResponse)
def get_public_key(user_id: UUID, db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    return PublicKeyResponse(
        user_id=str(user.id),
        email=user.email,
        public_key=user.public_key,
    )