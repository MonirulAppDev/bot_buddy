import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TaskLog(Base):
    __tablename__ = "task_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    persona_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("personas.id", ondelete="SET NULL"), nullable=True)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)  # like, love_react, comment, view, follow
    status: Mapped[str] = mapped_column(String(30), default="success")    # success, failed
    execution_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    order = relationship("Order", back_populates="task_logs")
    persona = relationship("Persona", back_populates="task_logs")
