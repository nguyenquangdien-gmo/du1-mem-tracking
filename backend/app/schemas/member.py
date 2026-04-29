from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class MemberBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=150)
    email: EmailStr
    department_id: int
    phone: str | None = Field(None, max_length=20)
    default_role: str | None = Field(None, max_length=80)
    other_roles: list[str] = []



class MemberCreate(MemberBase):
    pass


class MemberUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=150)
    email: EmailStr | None = None
    department_id: int | None = None
    phone: str | None = Field(None, max_length=20)
    default_role: str | None = Field(None, max_length=80)
    other_roles: list[str] | None = None



class MemberOut(MemberBase):
    id: int
    is_deleted: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
    department_name: str | None = None
    department_code: str | None = None

    model_config = ConfigDict(from_attributes=True)


class MemberSimple(BaseModel):
    id: int
    full_name: str
    email: str
    department_id: int
    department_code: str | None = None
    phone: str | None = None
    default_role: str | None = None
    other_roles: list[str] = []


    model_config = ConfigDict(from_attributes=True)
