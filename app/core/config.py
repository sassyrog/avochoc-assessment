from pydantic_settings import BaseSettings, SettingsConfigDict

API_V1_PREFIX = "/api/v1"


class Settings(BaseSettings):
    APP_NAME: str = "AvoChoc Assessment"
    DATABASE_URL: str
    REDIS_URL: str

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int
    ENVIRONMENT: str = "development"

    # AI Configuration
    AI_PROVIDER: str = "ollama"  # ollama | openai | anthropic | lmstudio
    AI_MODEL: str = "llava"
    AI_ENDPOINT: str
    AI_API_KEY: str | None = None

    model_config = SettingsConfigDict(
        extra="ignore", env_file=".env", env_file_encoding="utf-8"
    )


settings = Settings()
