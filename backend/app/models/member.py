import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func, JSON

from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Member(Base):
    __tablename__ = "member"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("user.id"), nullable=True, index=True)
    
    department_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("department.id"), nullable=False, index=True
    )
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    default_role: Mapped[str | None] = mapped_column(String(80))  # Job title
    other_roles: Mapped[list[str] | None] = mapped_column(JSON, default=[])
    is_deleted: Mapped[int] = mapped_column(Integer, default=0, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="member")
    department = relationship("Department", back_populates="members")
    project_assignments = relationship(
        "ProjectMember", back_populates="member", cascade="all,delete-orphan"
    )
    task_assignments = relationship(
        "TaskMember", back_populates="member", cascade="all,delete-orphan"
    )
