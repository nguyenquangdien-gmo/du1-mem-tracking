from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Task(Base):
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("project.id"), nullable=False, index=True)
    department_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("department.id"), index=True)
    pm_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("member.id"), index=True)
    start_date: Mapped[date | None] = mapped_column(Date)
    deadline: Mapped[date | None] = mapped_column(Date)
    jira_link: Mapped[str | None] = mapped_column(String(500))
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    status: Mapped[str] = mapped_column(String(20), default="todo", index=True)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    project = relationship("Project", back_populates="tasks")
    department = relationship("Department", back_populates="tasks")
    pm = relationship("Member", foreign_keys=[pm_id])
    members = relationship("TaskMember", back_populates="task", cascade="all,delete-orphan")


TASK_STATUSES = ("todo", "in_progress", "review", "done", "archived")
TASK_PRIORITIES = ("low", "medium", "high", "urgent")
