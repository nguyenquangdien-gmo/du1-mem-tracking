from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ProjectStatus = Literal["planning", "active", "on_hold", "completed", "cancelled"]


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    department_id: int
    pm_id: int
    start_date: date | None = None
    expected_end_date: date | None = None
    description: str | None = None
    status: ProjectStatus = "planning"
    is_important: int = 0
    chatops_group_id: str | None = Field(None, max_length=100)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    department_id: int | None = None
    pm_id: int | None = None
    start_date: date | None = None
    expected_end_date: date | None = None
    description: str | None = None
    status: ProjectStatus | None = None
    is_important: int | None = None
    chatops_group_id: str | None = Field(None, max_length=100)


class ProjectOut(ProjectBase):
    id: int
    is_deleted: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
    department_name: str | None = None
    pm_name: str | None = None
    task_count: int = 0
    task_done_count: int = 0
    overdue_task_count: int = 0
    active_member_count: int = 0

    model_config = ConfigDict(from_attributes=True)
