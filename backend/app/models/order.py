import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    service_id: Mapped[int] = mapped_column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False)
    target_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    delivered_count: Mapped[int] = mapped_column(Integer, default=0)
    remains_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="Pending", index=True)  # Pending, In progress, Completed, Canceled, Partial
    comments: Mapped[str] = mapped_column(Text, default="", nullable=True)
    drip_feed: Mapped[bool] = mapped_column(Boolean, default=False)
    interval_seconds: Mapped[int] = mapped_column(Integer, default=5)
    runs: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    service = relationship("Service", back_populates="orders")
    task_logs = relationship("TaskLog", back_populates="order", cascade="all, delete-orphan")
