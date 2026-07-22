import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # application configuration
    APP_NAME: str = "Enterprise IT Operations Automation Platform"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"  # nosec B104

    PORT: int = 8000

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

    # SMS Notification Configuration
    NOTIFICATION_PROVIDER: str = "console"
    SMS_API_KEY: str | None = None
    SMS_ACCOUNT_SID: str | None = None
    SMS_BASE_URL: str = "https://api.sms-provider.com/v1"
    SMS_SENDER_ID: str = "IT-OPS"
    SMS_TIMEOUT_SECONDS: float = 5.0
    SMS_RETRY_COUNT: int = 3
    SMS_TEST_RECIPIENT: str | None = None

    # Authentication Configuration
    AUTH_PROVIDER: str = "local"
    ENTRA_TENANT_ID: str | None = None
    ENTRA_CLIENT_ID: str | None = None
    ENTRA_REDIRECT_URI: str | None = None

    # Local JWT configuration
    JWT_SECRET_KEY: str = "secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440


settings = Settings()

if not os.path.exists("/.dockerenv"):
    if "@postgres:" in settings.DATABASE_URL:
        settings.DATABASE_URL = settings.DATABASE_URL.replace(
            "@postgres:", "@127.0.0.1:"
        )
    elif "postgresql://postgres:postgres@postgres:" in settings.DATABASE_URL:
        settings.DATABASE_URL = settings.DATABASE_URL.replace(
            "postgresql://postgres:postgres@postgres:",
            "postgresql://postgres:postgres@127.0.0.1:",
        )

    if settings.REDIS_HOST == "redis":
        settings.REDIS_HOST = "127.0.0.1"

    if settings.REDIS_URL:
        if "@redis:" in settings.REDIS_URL:
            settings.REDIS_URL = settings.REDIS_URL.replace("@redis:", "@127.0.0.1:")
        elif "redis://redis:" in settings.REDIS_URL:
            settings.REDIS_URL = settings.REDIS_URL.replace(
                "redis://redis:", "redis://127.0.0.1:"
            )
