import enum
from datetime import datetime
from sqlalchemy import DateTime, Enum, Integer, String, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base

class SystemRole(str, enum.Enum):
    ADMIN = "admin"
    PM = "pm"
    MEMBER = "member"

class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    system_role: Mapped[SystemRole] = mapped_column(
        Enum(SystemRole), default=SystemRole.MEMBER, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    mattermost_id: Mapped[str | None] = mapped_column(String(50))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationship to Member
    member = relationship("Member", back_populates="user", uselist=False)
