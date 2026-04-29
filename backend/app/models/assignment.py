from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class ProjectMember(Base):
    __tablename__ = "project_member"
    __table_args__ = (UniqueConstraint("project_id", "member_id", name="uq_project_member"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("project.id"), nullable=False, index=True)
    member_id: Mapped[int] = mapped_column(Integer, ForeignKey("member.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    expected_end_date: Mapped[date | None] = mapped_column(Date)
    is_hidden: Mapped[int] = mapped_column(Integer, default=0, index=True)
    hidden_reason: Mapped[str | None] = mapped_column(String(255))
    assigned_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    project = relationship("Project", back_populates="members")
    member = relationship("Member", back_populates="project_assignments")


class TaskMember(Base):
    __tablename__ = "task_member"
    __table_args__ = (UniqueConstraint("task_id", "member_id", name="uq_task_member"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("task.id"), nullable=False, index=True)
    member_id: Mapped[int] = mapped_column(Integer, ForeignKey("member.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    expected_end_date: Mapped[date | None] = mapped_column(Date)
    is_hidden: Mapped[int] = mapped_column(Integer, default=0, index=True)
    hidden_reason: Mapped[str | None] = mapped_column(String(255))
    notified: Mapped[int] = mapped_column(Integer, default=0)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    task = relationship("Task", back_populates="members")
    member = relationship("Member", back_populates="task_assignments")
