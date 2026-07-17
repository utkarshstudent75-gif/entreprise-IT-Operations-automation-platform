from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # application configuration
    APP_NAME: str = "Enterprise IT Operations Automation Platform"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database Configuration
    DATABASE_URL: str = "postgresql://postgres:postgres@postgres:5432/eitoap"

    # OTP Configuration
    OTP_LENGTH: int = 6
    OTP_EXPIRY_MINUTES: int = 5
    OTP_MAX_ATTEMPTS: int = 3

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
