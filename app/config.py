from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SYNC_DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_REDIRECT_URI: str
    LLM_MODEL_PATH: str

    class Config:
        env_file = ".env"

settings = Settings()