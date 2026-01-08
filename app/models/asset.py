from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Text, ForeignKey
from uuid import uuid4
from datetime import date
from app.models.base import Base


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str]
    type: Mapped[str]
    description: Mapped[str | None] = mapped_column(Text)
    count: Mapped[int] = mapped_column(default=1)
    model: Mapped[str | None]
    serial_number: Mapped[str | None]
    check_in_date: Mapped[date]
    check_out_date: Mapped[date | None]

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    owner = relationship("User", back_populates="assets")
