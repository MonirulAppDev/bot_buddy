import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Persona(Base):
    __tablename__ = "personas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    avatar_url: Mapped[str] = mapped_column(String(500), default="")
    platform: Mapped[str] = mapped_column(String(50), default="facebook", index=True)
    locale: Mapped[str] = mapped_column(String(20), default="en_US")
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)  # active, cooldown, retired
    total_actions: Mapped[int] = mapped_column(Integer, default=0)
    extra_metadata: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    task_logs = relationship("TaskLog", back_populates="persona")
