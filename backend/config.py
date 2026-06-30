from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://ai:ai123@localhost:5432/school_ai"
    DEEPSEEK_API_KEY: str = ""
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_API_URL: str = "https://api.example.com/v1/embeddings"
    EMBEDDING_DIMENSION: int = 1024
    FILE_STORAGE_PATH: str = "./uploads"
    JWT_SECRET: str = "school-ai-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
