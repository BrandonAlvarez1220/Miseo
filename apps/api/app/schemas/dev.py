from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserRead


class DevLoginRequest(BaseModel):
    email: EmailStr
    display_name: str | None = Field(default=None, max_length=80)


class DevLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead
