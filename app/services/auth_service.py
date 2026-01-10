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

    async def login(
        self, session, email, password, ip_address: str | None, background_tasks
    ):
        user = await session.scalar(select(User).where(User.email == email))
        if not user or not verify_password(password, user.hashed_password):
            return None, None

        # Check for IP mismatch and alert
        if user.last_ip and ip_address and user.last_ip != ip_address:
            from app.services.email_service import EmailService

            background_tasks.add_task(
                EmailService.send_login_alert, user.email, ip_address
            )

        # Update last IP (if provided)
        if ip_address:
            user.last_ip = ip_address
            session.add(user)
            await session.commit()

        token = create_token(str(user.id))
        return token, user
