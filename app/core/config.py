from pydantic_settings import BaseSettings
import logging

class Settings(BaseSettings):
    PROJECT_NAME: str = "Remind Anyone Backend"
    DATABASE_URL: str
    
    # Google SSO (Optional for initial setup but good to have prepared)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    SECRET_KEY: str = "changethis"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()


logging.basicConfig(level=logging.INFO)