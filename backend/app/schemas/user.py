from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from ..models.user import SystemRole

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    system_role: SystemRole = SystemRole.MEMBER
    is_active: bool = True
    mattermost_id: str | None = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserUpdate(BaseModel):
    username: str | None = Field(None, min_length=3, max_length=50)
    email: EmailStr | None = None
    system_role: SystemRole | None = None
    is_active: bool | None = None
    mattermost_id: str | None = None
    password: str | None = Field(None, min_length=6)

class UserOut(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    email: EmailStr
    otp: str
    new_password: str = Field(..., min_length=6)
