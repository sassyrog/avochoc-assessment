import pytest
from datetime import date
from app.services.asset_service import AssetService
from app.models.user import User
from app.core.security import hash_password


@pytest.mark.asyncio
async def test_create_asset_with_new_fields(session):
    service = AssetService()

    # Create an owner
    owner = User(email="owner@example.com", hashed_password=hash_password("password"))
    session.add(owner)
    await session.commit()

    asset = await service.create_asset(
        session,
        name="Laptop",
        type="Hardware",
        check_in_date=date(2023, 1, 1),
        description="A test laptop",
        count=5,
        model="X1 Carbon",
        serial_number="SN123456",
        owner_id=owner.id,
    )

    assert asset.id is not None
    assert asset.name == "Laptop"
    assert asset.count == 5
    assert asset.model == "X1 Carbon"
    assert asset.serial_number == "SN123456"
    assert asset.check_in_date == date(2023, 1, 1)


@pytest.mark.asyncio
async def test_update_asset_fields(session):
    service = AssetService()

    # Create owner
    owner = User(email="owner2@example.com", hashed_password=hash_password("password"))
    session.add(owner)
    await session.commit()

    # Create initial asset
    asset = await service.create_asset(
        session,
        name="Phone",
        type="Device",
        check_in_date=date(2023, 1, 1),
        owner_id=owner.id,
    )

    # Update fields
    updated = await service.update_asset(
        session,
        asset,
        count=10,
        model="Pixel 6",
        serial_number="Pixel-123",
        check_out_date=date(2023, 2, 1),
    )

    assert updated.count == 10
    assert updated.model == "Pixel 6"
    assert updated.serial_number == "Pixel-123"
    assert updated.check_out_date == date(2023, 2, 1)
