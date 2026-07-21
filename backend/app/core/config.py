from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # application configuration
    APP_NAME: str
    APP_VERSION: str
    ENVIRONMENT: str
    DEBUG: bool
    HOST: str
    PORT: int

    # Database Configuration
    DATABASE_URL: str

    # Redis Configuration
    REDIS_URL: str | None = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    # OTP Configuration
    OTP_LENGTH: int = 6
    OTP_EXPIRY_MINUTES: int = 5
    OTP_MAX_ATTEMPTS: int = 3

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
