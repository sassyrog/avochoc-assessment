from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import check_db_connection, engine
from app.core.redis import check_redis_connection
from app.core.config import API_V1_PREFIX
import app.core.logging  # noqa

from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.assets import router as assets_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await check_db_connection()
    await check_redis_connection()
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.include_router(health_router, prefix=API_V1_PREFIX)
app.include_router(auth_router, prefix=API_V1_PREFIX)
app.include_router(assets_router, prefix=API_V1_PREFIX)
