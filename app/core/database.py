import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,  # Number of connections to keep open
    max_overflow=10,  # Additional connections if pool is full
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_timeout=30,  # Wait 30s for connection from pool
    echo=False,  # Set to True for SQL debugging
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session


async def check_db_connection():
    """Test database connection"""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        logger.info("db connected")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
