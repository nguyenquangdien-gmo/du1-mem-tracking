from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=2, max_length=20)


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    code: str | None = Field(None, min_length=2, max_length=20)


class DepartmentOut(DepartmentBase):
    id: int
    created_at: datetime | None = None
    is_deleted: int = 0

    model_config = ConfigDict(from_attributes=True)
