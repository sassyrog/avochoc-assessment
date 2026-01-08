from fastapi import FastAPI
from app.core.database import check_db_connection
from app.core.redis import check_redis_connection
import app.core.logging  # noqa

from app.api.routes.health import router as health_router


app = FastAPI()


@app.on_event("startup")
async def startup():
    await check_db_connection()
    await check_redis_connection()


V1_PREFIX = "/api/v1"


app.include_router(health_router, prefix=V1_PREFIX)
