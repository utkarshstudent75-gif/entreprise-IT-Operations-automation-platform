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

    # Microsoft Entra ID Integration
    ENTRA_TENANT_ID: str | None = None
    ENTRA_CLIENT_ID: str | None = None
    ENTRA_CLIENT_SECRET: str | None = None
    ENTRA_REDIRECT_URI: str | None = None
    GRAPH_ENDPOINT: str = "https://graph.microsoft.com/v1.0"
    USE_MANAGED_IDENTITY: bool = False

    # Microsoft Graph Integration (Alternative environment variables)
    TENANT_ID: str | None = None
    CLIENT_ID: str | None = None
    CLIENT_SECRET: str | None = None
    GRAPH_SCOPES: str | None = "https://graph.microsoft.com/.default"
    KEYVAULT_NAME: str | None = None
    AUTHORITY: str | None = None
    REDIRECT_URI: str | None = None
    API_AUDIENCE: str | None = None

    # Password Policy Configuration
    PASSWORD_MIN_LENGTH: int = 12
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    PASSWORD_FORCE_CHANGE_ON_NEXT_SIGNIN: bool = True

    # JWT Authentication Configuration
    JWT_SECRET_KEY: str = "secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440


def retrieve_secrets_from_key_vault(settings_obj: Settings) -> None:
    """Retrieves configuration values from Azure Key Vault if KEYVAULT_NAME is set.

    Supports fallback to environment variables in case of local development or connection failures.
    """
    keyvault_name = settings_obj.KEYVAULT_NAME
    if not keyvault_name:
        return

    try:
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient
    except ImportError:
        # If azure SDK is not present, skip
        return

    vault_url = f"https://{keyvault_name}.vault.azure.net"
    try:
        # DefaultAzureCredential supports environment variables, Workload Identity, managed identity, CLI, etc.
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=vault_url, credential=credential)

        # 1. Fetch MS Graph Credentials
        try:
            settings_obj.CLIENT_ID = client.get_secret("msgraph-client-id").value
            settings_obj.ENTRA_CLIENT_ID = settings_obj.CLIENT_ID
        except Exception:
            pass

        try:
            settings_obj.CLIENT_SECRET = client.get_secret(
                "msgraph-client-secret"
            ).value
            settings_obj.ENTRA_CLIENT_SECRET = settings_obj.CLIENT_SECRET
        except Exception:
            pass

        try:
            settings_obj.TENANT_ID = client.get_secret("msgraph-tenant-id").value
            settings_obj.ENTRA_TENANT_ID = settings_obj.TENANT_ID
        except Exception:
            pass

        try:
            settings_obj.AUTHORITY = client.get_secret("sso-authority").value
        except Exception:
            pass

        try:
            settings_obj.REDIRECT_URI = client.get_secret("sso-redirect-uri").value
            settings_obj.ENTRA_REDIRECT_URI = settings_obj.REDIRECT_URI
        except Exception:
            pass

        try:
            settings_obj.API_AUDIENCE = client.get_secret("sso-api-audience").value
        except Exception:
            pass

        # 2. Fetch Database Credentials
        try:
            db_host = client.get_secret("database-host").value
            db_port = client.get_secret("database-port").value
            db_name = client.get_secret("database-name").value
            db_user = client.get_secret("database-username").value
            db_pass = client.get_secret("database-password").value
            if all([db_host, db_port, db_name, db_user, db_pass]):
                settings_obj.DATABASE_URL = (
                    f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
                )
        except Exception:
            pass

        # 3. Fetch Redis Credentials
        try:
            redis_host = client.get_secret("redis-host").value
            redis_port = client.get_secret("redis-port").value
            redis_key = client.get_secret("redis-primary-key").value
            if all([redis_host, redis_port, redis_key]):
                settings_obj.REDIS_HOST = redis_host
                settings_obj.REDIS_PORT = int(redis_port)
                settings_obj.REDIS_PASSWORD = redis_key
                settings_obj.REDIS_URL = (
                    f"redis://:{redis_key}@{redis_host}:{redis_port}/0"
                )
        except Exception:
            pass

        # 4. Fetch SMS Notification Credentials
        try:
            sms_api_key = client.get_secret("sms-provider-api-key").value
            sms_sid = client.get_secret("sms-provider-account-sid").value
            if sms_api_key:
                settings_obj.SMS_API_KEY = sms_api_key
            if sms_sid:
                settings_obj.SMS_ACCOUNT_SID = sms_sid
        except Exception:
            pass

    except Exception as e:
        import logging

        logger = logging.getLogger("itpa")
        logger.warning(
            "Azure Key Vault client initialization failed: %s. Using environment variables.",
            str(e),
        )


settings = Settings()

# Map the alternative parameters if configured via environment variables
if settings.TENANT_ID and not settings.ENTRA_TENANT_ID:
    settings.ENTRA_TENANT_ID = settings.TENANT_ID
if settings.CLIENT_ID and not settings.ENTRA_CLIENT_ID:
    settings.ENTRA_CLIENT_ID = settings.CLIENT_ID
if settings.CLIENT_SECRET and not settings.ENTRA_CLIENT_SECRET:
    settings.ENTRA_CLIENT_SECRET = settings.CLIENT_SECRET
if settings.REDIRECT_URI and not settings.ENTRA_REDIRECT_URI:
    settings.ENTRA_REDIRECT_URI = settings.REDIRECT_URI

retrieve_secrets_from_key_vault(settings)

if not os.path.exists("/.dockerenv") and not os.environ.get("KUBERNETES_SERVICE_HOST"):
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
