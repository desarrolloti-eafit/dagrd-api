from pydantic import BaseModel, EmailStr, Field

from app.models.user import RoleEnum


# ---------------------------------------------------------------------------
# Auth schemas
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, examples=["admin"])
    password: str = Field(..., min_length=1, examples=["secret"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# User schemas
# ---------------------------------------------------------------------------

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: RoleEnum
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserRead(UserBase):
    id: int

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Token payload (internal use)
# ---------------------------------------------------------------------------

class TokenPayload(BaseModel):
    sub: str       # username
    role: RoleEnum
