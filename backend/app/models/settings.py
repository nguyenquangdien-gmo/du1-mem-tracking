from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base

class SystemSettings(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    idle_report_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    idle_report_morning_time: Mapped[str] = mapped_column(String(10), default="08:00")
    idle_report_evening_time: Mapped[str] = mapped_column(String(10), default="17:00")
    late_report_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    late_report_time: Mapped[str] = mapped_column(String(10), default="18:00")
    chatops_pm_group_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
