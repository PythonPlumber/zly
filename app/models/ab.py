import random
import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ABVariant(Base):
    __tablename__ = "ab_variants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    link_id: Mapped[str] = mapped_column(String(36), ForeignKey("links.id", ondelete="CASCADE"), nullable=False, index=True)
    destination_url: Mapped[str] = mapped_column(Text, nullable=False)
    weight: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    is_default: Mapped[bool] = mapped_column(default=False, nullable=False)

    link = relationship("Link", backref="variants")
