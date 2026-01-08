from pydantic import BaseModel

class AssetOut(BaseModel):
    id: str
    name: str
    type: str
    description: str | None

    class Config:
        from_attributes = True
