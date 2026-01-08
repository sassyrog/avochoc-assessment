from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from app.core.config import settings, API_V1_PREFIX
from app.core.database import get_session
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{API_V1_PREFIX}/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session=Depends(get_session),
):
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(401, "Invalid token")

    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(401, "User not found")
    return user
