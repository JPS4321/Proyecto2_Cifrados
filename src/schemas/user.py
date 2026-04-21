from pydantic import BaseModel, EmailStr

class PublicKeyResponse(BaseModel):
    user_id: str
    email: EmailStr
    public_key: str