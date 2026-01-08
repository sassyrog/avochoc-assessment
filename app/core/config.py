from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "AvoChoc Assessment"

    class Config:
        env_file = ".env"


settings = Settings()
