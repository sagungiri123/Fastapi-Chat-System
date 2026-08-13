from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        
settings = Settings()

# This is the heart of the configuration system.
"""
The BaseSettings loads and validates the postgreSQL credentials
and SQLAlchemy uses the resulting configurations to create the DB connections.

"""