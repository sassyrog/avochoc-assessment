from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from datetime import date
from app.models.asset import Asset
from app.models.user import User
from app.core.security import hash_password
import uuid


class AssetService:
    async def list_assets(self, session):
        """List all assets"""
        return (await session.scalars(select(Asset))).all()

    async def get_asset(self, session, asset_id: str):
        """Get a single asset by ID"""
        return await session.scalar(select(Asset).where(Asset.id == asset_id))

    async def resolve_owner(
        self, session, owner_id: int | None, owner_email: str | None, current_user
    ):
        """
        Resolve asset owner by ID, email, or use current user.

        Priority order:
        1. If owner_id provided → validate and use that ID
        2. Else if owner_email provided → find user by email, or create if not exists
        3. Else → use current authenticated user

        Returns: owner_id (int)
        """
        if owner_id:
            # Direct ID provided - validate user exists
            user = await session.scalar(select(User).where(User.id == owner_id))
            if not user:
                raise ValueError(f"User with ID {owner_id} not found")
            return owner_id

        if owner_email:
            # Try to find existing user by email
            user = await session.scalar(select(User).where(User.email == owner_email))

            if not user:
                # Create new user if doesn't exist
                # Generate random password since this is a non-interactive user creation
                random_password = str(uuid.uuid4())
                user = User(
                    email=owner_email, hashed_password=hash_password(random_password)
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)

            return user.id

        # Use current authenticated user
        return current_user.id

    async def create_asset(
        self,
        session,
        name: str,
        type: str,
        check_in_date: date,
        description: str | None = None,
        count: int = 1,
        model: str | None = None,
        serial_number: str | None = None,
        check_out_date: date | None = None,
        owner_id: int | None = None,
        owner_email: str | None = None,
        current_user=None,
    ):
        """Create a new asset with optional owner_id or owner_email"""
        try:
            # Resolve owner
            resolved_owner_id = await self.resolve_owner(
                session, owner_id, owner_email, current_user
            )

            asset = Asset(
                name=name,
                type=type,
                description=description,
                count=count,
                model=model,
                serial_number=serial_number,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                owner_id=resolved_owner_id,
            )
            session.add(asset)
            await session.commit()
            await session.refresh(asset)
            return asset
        except SQLAlchemyError:
            await session.rollback()
            raise

    async def update_asset(
        self,
        session,
        asset: Asset,
        name: str | None = None,
        type: str | None = None,
        description: str | None = None,
        count: int | None = None,
        model: str | None = None,
        serial_number: str | None = None,
        check_in_date: date | None = None,
        check_out_date: date | None = None,
    ):
        """Update an asset"""
        try:
            if name is not None:
                asset.name = name
            if type is not None:
                asset.type = type
            if description is not None:
                asset.description = description
            if count is not None:
                asset.count = count
            if model is not None:
                asset.model = model
            if serial_number is not None:
                asset.serial_number = serial_number
            if check_in_date is not None:
                asset.check_in_date = check_in_date
            if check_out_date is not None:
                asset.check_out_date = check_out_date
            await session.commit()
            await session.refresh(asset)
            return asset
        except SQLAlchemyError:
            await session.rollback()
            raise

    async def delete_asset(self, session, asset: Asset):
        """Delete an asset"""
        try:
            await session.delete(asset)
            await session.commit()
            return True
        except SQLAlchemyError:
            await session.rollback()
            raise
