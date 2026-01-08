from pydantic import BaseModel, EmailStr


class AssetCreate(BaseModel):
    name: str
    type: str
    description: str | None = None
    owner_id: int | None = None  # Optional: direct user ID reference
    owner_email: EmailStr | None = None  # Optional: match or create user by email


class AssetUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    description: str | None = None


class AssetOut(BaseModel):
    id: str
    name: str
    type: str
    description: str | None
    owner_id: int

    class Config:
        from_attributes = True
