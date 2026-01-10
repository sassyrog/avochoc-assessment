from fastapi import APIRouter, Depends, HTTPException, UploadFile
from app.core.database import get_session
from app.schemas.asset import AssetCreate, AssetUpdate, AssetOut
from app.schemas.response import SuccessResponse
from app.services.asset_service import AssetService
from app.api.deps import get_current_user
from app.core.cache import cache_response, invalidate_cache

router = APIRouter(prefix="/assets")


@router.get("", response_model=SuccessResponse[list[AssetOut]])
@cache_response(key_pattern="assets:list", expire=60)
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


@router.post("", response_model=SuccessResponse[AssetOut], status_code=201)
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
        data.check_in_date,
        data.description,
        data.count,
        data.model,
        data.serial_number,
        data.check_out_date,
        owner_id=data.owner_id,
        owner_email=data.owner_email,
        current_user=user,
    )
    await invalidate_cache("assets:list")
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
        session,
        asset,
        data.name,
        data.type,
        data.description,
        data.count,
        data.model,
        data.serial_number,
        data.check_in_date,
        data.check_out_date,
    )
    await invalidate_cache("assets:list")
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
    await invalidate_cache("assets:list")


@router.post("/{asset_id}/upload-image", response_model=SuccessResponse[AssetOut])
async def upload_asset_image(
    asset_id: str,
    image: UploadFile,
    session=Depends(get_session),
    user=Depends(get_current_user),
):
    """Upload an image and generate AI description for the asset."""
    from app.services.ai_service import (
        AIService,
        AIProviderError,
        validate_image,
        MAX_IMAGE_SIZE,
    )

    # Get the asset
    svc = AssetService()
    asset = await svc.get_asset(session, asset_id)
    if not asset:
        raise HTTPException(404, "Asset not found")

    # Read and validate the image
    image_bytes = await image.read()
    try:
        validate_image(image.content_type, len(image_bytes))
    except ValueError as e:
        raise HTTPException(400, str(e))

    # Ensure we don't process files that are too large
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(
            400,
            f"Image size exceeds maximum allowed size of {MAX_IMAGE_SIZE / 1024 / 1024:.0f} MB",
        )

    # Generate AI description
    ai_service = AIService()
    try:
        description = await ai_service.describe_asset_image(
            image_bytes, image.content_type or "image/jpeg"
        )
    except AIProviderError as e:
        raise HTTPException(503, f"AI service unavailable: {e}")

    # Update the asset with the generated description
    updated_asset = await svc.update_asset(session, asset, description=description)
    await invalidate_cache("assets:list")

    return SuccessResponse(
        message="Asset image processed and description updated",
        code=200,
        data=updated_asset,
    )
