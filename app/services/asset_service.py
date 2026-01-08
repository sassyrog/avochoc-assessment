from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from app.models.asset import Asset

class AssetService:
    async def list_assets(self, session, user):
        return (await session.scalars(
            select(Asset).where(Asset.owner_id == user.id)
        )).all()

    async def update_description(self, session, asset: Asset, description: str):
        try:
            asset.description = description
            await session.commit()
        except SQLAlchemyError:
            await session.rollback()
            raise
