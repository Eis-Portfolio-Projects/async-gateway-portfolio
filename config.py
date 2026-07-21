import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_KEY: str = os.getenv("GATEWAY_API_KEY", "prod_secret_token_123789")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    TARGET_API_URL: str = os.getenv("TARGET_API_URL", "https://httpbin.org/post")
    RATE_LIMIT_CALLS: int = 60
    RATE_LIMIT_PERIOD: int = 60

settings = Settings()