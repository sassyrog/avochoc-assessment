from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_session
from app.schemas.user import UserCreate, LoginResponse
from app.schemas.response import SuccessResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth")


@router.post(
    "/register", response_model=SuccessResponse[LoginResponse], status_code=201
)
async def register(data: UserCreate, session=Depends(get_session)):
    svc = AuthService()
    await svc.register(session, data.email, data.password, data.name, data.phone)
    token, authenticated_user = await svc.login(session, data.email, data.password)
    return SuccessResponse(
        message="User registered successfully",
        code=201,
        data=LoginResponse(
            access_token=token,
            user={
                "id": authenticated_user.id,
                "email": authenticated_user.email,
                "name": authenticated_user.name,
                "phone": authenticated_user.phone,
            },
        ),
    )


@router.post("/login", response_model=SuccessResponse[LoginResponse])
async def login(data: UserCreate, session=Depends(get_session)):
    svc = AuthService()
    token, user = await svc.login(session, data.email, data.password)
    if not token:
        raise HTTPException(401, "Invalid credentials")
    return SuccessResponse(
        message="Login successful",
        code=200,
        data=LoginResponse(
            access_token=token,
            user={
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "phone": user.phone,
            },
        ),
    )
