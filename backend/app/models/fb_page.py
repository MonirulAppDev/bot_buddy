import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FBPage(Base):
    __tablename__ = "fb_pages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_account_id: Mapped[str] = mapped_column(String(36), ForeignKey("fb_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    page_name: Mapped[str] = mapped_column(String(150), nullable=False)
    page_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    category: Mapped[str] = mapped_column(String(100), default="Digital Creator")
    avatar_url: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[str] = mapped_column(String(30), default="active")
    total_likes_given: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    parent_account = relationship("FBAccount", back_populates="pages")
