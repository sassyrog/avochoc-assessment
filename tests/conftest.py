import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models.base import Base

from app.models import User, Asset  # noqa
from app.core.database import get_session

# I use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(name="session")
async def session_fixture():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = async_sessionmaker(
        autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(name="client")
async def client_fixture(session):
    async def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(session):
    from app.models.user import User
    from app.core.security import hash_password

    user = User(
        email="test@example.com",
        hashed_password=hash_password("password"),
        name="Test User",
        phone="1234567890",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def auth_token(test_user):
    from app.core.security import create_token

    return create_token(str(test_user.id))


@pytest.fixture
async def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
