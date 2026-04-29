from datetime import date
from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class WorkingCalendar(Base):
    __tablename__ = "working_calendar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    calendar_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # holiday, leave, special
    member_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("member.id"), nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)

    member = relationship("Member")

CALENDAR_TYPES = ("holiday", "leave", "special")
