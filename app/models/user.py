from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str]
    name: Mapped[str | None]
    phone: Mapped[str | None]
    last_ip: Mapped[str | None]

    assets = relationship("Asset", back_populates="owner")
