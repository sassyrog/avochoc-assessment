from pydantic import BaseModel, EmailStr
from datetime import date


class AssetCreate(BaseModel):
    name: str
    type: str
    description: str | None = None
    count: int = 1
    model: str | None = None
    serial_number: str | None = None
    check_in_date: date
    check_out_date: date | None = None
    owner_id: int | None = None  # Optional: direct user ID reference
    owner_email: EmailStr | None = None  # Optional: match or create user by email


class AssetUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    description: str | None = None
    count: int | None = None
    model: str | None = None
    serial_number: str | None = None
    check_in_date: date | None = None
    check_out_date: date | None = None


class AssetOut(BaseModel):
    id: str
    name: str
    type: str
    description: str | None
    count: int
    model: str | None
    serial_number: str | None
    check_in_date: date
    check_out_date: date | None
    owner_id: int

    class Config:
        from_attributes = True
