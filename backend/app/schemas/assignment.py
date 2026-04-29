from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class AssignmentBase(BaseModel):
    role: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    expected_end_date: date | None = None


class AssignmentCreate(AssignmentBase):
    member_id: int


class AssignmentUpdate(BaseModel):
    role: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    expected_end_date: date | None = None
    is_hidden: bool | None = None
    hidden_reason: str | None = Field(None, max_length=255)


class ProjectMemberOut(BaseModel):
    id: int
    project_id: int
    member_id: int
    role: str
    description: str | None = None
    expected_end_date: date | None = None
    is_hidden: bool = False
    hidden_reason: str | None = None
    assigned_at: datetime | None = None
    updated_at: datetime | None = None

    # joined fields
    member_name: str | None = None
    member_email: str | None = None
    department_code: str | None = None
    project_name: str | None = None

    action: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TaskMemberOut(BaseModel):
    id: int
    task_id: int
    member_id: int
    role: str
    expected_end_date: date | None = None
    is_hidden: bool = False
    hidden_reason: str | None = None
    assigned_at: datetime | None = None
    updated_at: datetime | None = None

    member_name: str | None = None
    member_email: str | None = None
    department_code: str | None = None
    task_name: str | None = None
    project_id: int | None = None
    project_name: str | None = None

    action: str | None = None

    model_config = ConfigDict(from_attributes=True)


class MemberAssignments(BaseModel):
    member: dict
    projects: list[ProjectMemberOut]
    tasks: list[TaskMemberOut]
    stats: dict
