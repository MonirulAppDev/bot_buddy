from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), default="facebook", index=True)
    service_type: Mapped[str] = mapped_column(String(50), nullable=False)  # like, reaction, follower, view, comment, share
    rate_per_1000: Mapped[float] = mapped_column(Float, default=1.0)
    min_quantity: Mapped[int] = mapped_column(Integer, default=10)
    max_quantity: Mapped[int] = mapped_column(Integer, default=50000)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str] = mapped_column(Text, default="")
    default_interval_seconds: Mapped[int] = mapped_column(Integer, default=5)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    orders = relationship("Order", back_populates="service", cascade="all, delete-orphan")
