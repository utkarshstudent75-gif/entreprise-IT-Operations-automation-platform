from pydantic_settings import BaseSettings,SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    ENVIRONMENT: str
    DEBUG: bool
    HOST: str
    PORT: int    

    OTP_LENGTH: int = 6
    OTP_EXPIRY_MINUTES: int = 5
    OTP_MAX_ATTEMPTS: int = 3



    #OTP Configuration
    OTP_LENGTH: int = 6
    OTP_EXPIRY_MINUTES: int = 5
    OTP_MAX_ATTEMPTS: int = 3


    model_config = SettingsConfigDict(
            env_file=".env",
            case_sensitive=True
            
            )

settings = Settings()

