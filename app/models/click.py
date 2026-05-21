from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Click(Base):
    __tablename__ = "clicks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    link_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("links.id"), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    browser: Mapped[str | None] = mapped_column(String(50), nullable=True)
    browser_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    os: Mapped[str | None] = mapped_column(String(50), nullable=True)
    device_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    referrer: Mapped[str | None] = mapped_column(Text, nullable=True)
    referrer_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    variant_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    link = relationship("Link", back_populates="clicks")
