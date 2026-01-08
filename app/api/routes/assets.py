from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_session
from app.schemas.asset import AssetCreate, AssetUpdate, AssetOut
from app.schemas.response import SuccessResponse
from app.services.asset_service import AssetService
from app.api.deps import get_current_user

router = APIRouter(prefix="/assets")


@router.get("/", response_model=SuccessResponse[list[AssetOut]])
async def list_assets(
    session=Depends(get_session),
    user=Depends(get_current_user),
):
    svc = AssetService()
    assets = await svc.list_assets(session)
    return SuccessResponse(
        message="Assets retrieved successfully", code=200, data=assets
    )


@router.get("/{asset_id}", response_model=SuccessResponse[AssetOut])
async def get_asset(
    asset_id: str,
    session=Depends(get_session),
    user=Depends(get_current_user),
):
    svc = AssetService()
    asset = await svc.get_asset(session, asset_id)
    if not asset:
        raise HTTPException(404, "Asset not found")
    return SuccessResponse(message="Asset retrieved successfully", code=200, data=asset)


@router.post("/", response_model=SuccessResponse[AssetOut], status_code=201)
async def create_asset(
    data: AssetCreate,
    session=Depends(get_session),
    user=Depends(get_current_user),
):
    svc = AssetService()
    asset = await svc.create_asset(
        session,
        data.name,
        data.type,
        data.description,
        owner_id=data.owner_id,
        owner_email=data.owner_email,
        current_user=user,
    )
    return SuccessResponse(message="Asset created successfully", code=201, data=asset)


@router.put("/{asset_id}", response_model=SuccessResponse[AssetOut])
async def update_asset(
    asset_id: str,
    data: AssetUpdate,
    session=Depends(get_session),
    user=Depends(get_current_user),
):
    svc = AssetService()
    asset = await svc.get_asset(session, asset_id)
    if not asset:
        raise HTTPException(404, "Asset not found")

    updated_asset = await svc.update_asset(
        session, asset, data.name, data.type, data.description
    )
    return SuccessResponse(
        message="Asset updated successfully", code=200, data=updated_asset
    )


@router.delete("/{asset_id}", status_code=204)
async def delete_asset(
    asset_id: str,
    session=Depends(get_session),
    user=Depends(get_current_user),
):
    svc = AssetService()
    asset = await svc.get_asset(session, asset_id)
    if not asset:
        raise HTTPException(404, "Asset not found")

    await svc.delete_asset(session, asset)
