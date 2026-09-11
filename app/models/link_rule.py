import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class LinkRule(Base):
    __tablename__ = "link_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    link_id: Mapped[str] = mapped_column(String(36), ForeignKey("links.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # geo | device | os | language | referrer
    match_value: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g. "US", "mobile", "en"
    destination_url: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    link = relationship("Link", backref="rules")
