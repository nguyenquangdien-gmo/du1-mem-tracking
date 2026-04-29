from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TaskStatus = Literal["todo", "in_progress", "review", "done", "archived"]
TaskPriority = Literal["low", "medium", "high", "urgent"]


class TaskBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    project_id: int
    department_id: int | None = None
    pm_id: int | None = None
    start_date: date | None = None
    deadline: date | None = None
    jira_link: str | None = None
    priority: TaskPriority = "medium"
    status: TaskStatus = "todo"


class TaskCreate(TaskBase):
    member_ids: list[int] = []


class TaskUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    department_id: int | None = None
    pm_id: int | None = None
    start_date: date | None = None
    deadline: date | None = None
    jira_link: str | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    member_ids: list[int] | None = None


class TaskOut(TaskBase):
    id: int
    is_deleted: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
    project_name: str | None = None
    department_name: str | None = None
    pm_name: str | None = None
    active_member_count: int = 0

    model_config = ConfigDict(from_attributes=True)
