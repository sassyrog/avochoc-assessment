import logging
from fastapi import FastAPI
from app.core.database import check_db_connection
from app.core.redis import check_redis_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


@app.on_event("startup")
async def startup():
    await check_db_connection()
    await check_redis_connection()


@app.get("/health")
def health_check():
    return {"message": "Healthy!!!"}
