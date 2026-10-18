import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FBAccount(Base):
    __tablename__ = "fb_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_name: Mapped[str] = mapped_column(String(100), nullable=False)
    cookie_data: Mapped[str] = mapped_column(Text, nullable=False)  # c_user=...; xs=...;
    fb_user_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active")  # active, checkpoint, expired
    total_likes_given: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
