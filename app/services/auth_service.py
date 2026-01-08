from sqlalchemy import select
from app.models.user import User
from app.core.security import hash_password, verify_password, create_token


class AuthService:
    async def register(self, session, email, password, name=None, phone=None):
        user = User(
            email=email,
            hashed_password=hash_password(password),
            name=name,
            phone=phone,
        )
        session.add(user)
        await session.commit()
        return user

    async def login(self, session, email, password):
        user = await session.scalar(select(User).where(User.email == email))
        if not user or not verify_password(password, user.hashed_password):
            return None, None
        token = create_token(str(user.id))
        return token, user
