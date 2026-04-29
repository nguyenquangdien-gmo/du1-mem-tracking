from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Project(Base):
    __tablename__ = "project"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey("department.id"), nullable=False, index=True)
    pm_id: Mapped[int] = mapped_column(Integer, ForeignKey("member.id"), nullable=False, index=True)
    start_date: Mapped[date | None] = mapped_column(Date)
    expected_end_date: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="planning", index=True)
    is_important: Mapped[int] = mapped_column(Integer, default=0, index=True)
    chatops_group_id: Mapped[str | None] = mapped_column(String(100))
    is_deleted: Mapped[int] = mapped_column(Integer, default=0, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    department = relationship("Department", back_populates="projects")
    pm = relationship("Member", foreign_keys=[pm_id])
    tasks = relationship("Task", back_populates="project", cascade="all,delete-orphan")
    members = relationship("ProjectMember", back_populates="project", cascade="all,delete-orphan")


PROJECT_STATUSES = ("planning", "active", "on_hold", "completed", "cancelled")
