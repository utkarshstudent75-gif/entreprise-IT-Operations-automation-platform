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

        def _secret(name: str) -> str | None:
            """Read a secret, returning None when it is missing or a placeholder.

            Terraform/CI seed the vault with defaults such as
            "placeholder-msgraph-client-id" or "<injected-from-azure-keyvault>".
            Those must never override working configuration — in particular the
            placeholder Graph credentials would otherwise disable mock mode.
            """
            try:
                value = client.get_secret(name).value
            except Exception:
                return None  # nosec B110
            if value is None:
                return None
            value = value.strip()
            if not value:
                return None
            lowered = value.lower()
            if value.startswith("<") or any(
                marker in lowered for marker in ("placeholder", "change_me", "changeme")
            ):
                return None
            return value

        # 1. Fetch MS Graph Credentials
        client_id = _secret("msgraph-client-id")
        if client_id:
            settings_obj.CLIENT_ID = client_id
            settings_obj.ENTRA_CLIENT_ID = client_id

        client_secret = _secret("msgraph-client-secret")
        if client_secret:
            settings_obj.CLIENT_SECRET = client_secret
            settings_obj.ENTRA_CLIENT_SECRET = client_secret

        tenant_id = _secret("msgraph-tenant-id")
        if tenant_id:
            settings_obj.TENANT_ID = tenant_id
            settings_obj.ENTRA_TENANT_ID = tenant_id

        authority = _secret("sso-authority")
        if authority:
            settings_obj.AUTHORITY = authority

        redirect_uri = _secret("sso-redirect-uri")
        if redirect_uri:
            settings_obj.REDIRECT_URI = redirect_uri
            settings_obj.ENTRA_REDIRECT_URI = redirect_uri

        api_audience = _secret("sso-api-audience")
        if api_audience:
            settings_obj.API_AUDIENCE = api_audience

        # 2. Fetch Database Credentials
        db_host = _secret("database-host")
        db_port = _secret("database-port")
        db_name = _secret("database-name")
        db_user = _secret("database-username")
        db_pass = _secret("database-password")
        if all([db_host, db_port, db_name, db_user, db_pass]):
            # Preserve any query options (e.g. ?sslmode=require) from the
            # currently configured URL so TLS is not silently dropped when
            # the connection string is rebuilt from Key Vault.
            query = ""
            current_url = settings_obj.DATABASE_URL or ""
            if "?" in current_url:
                query = "?" + current_url.rsplit("?", 1)[1]
            settings_obj.DATABASE_URL = (
                f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/"
                f"{db_name}{query}"
            )

        # 3. Fetch Redis Credentials
        redis_host = _secret("redis-host")
        redis_port = _secret("redis-port")
        redis_key = _secret("redis-primary-key")
        if all([redis_host, redis_port, redis_key]):
            settings_obj.REDIS_HOST = redis_host
            settings_obj.REDIS_PORT = int(redis_port)
            settings_obj.REDIS_PASSWORD = redis_key
            # Azure Cache for Redis disables non-TLS traffic, so keep the
            # scheme (rediss://) of the currently configured URL.
            scheme = (
                "rediss://"
                if (settings_obj.REDIS_URL or "").startswith("rediss://")
                else "redis://"
            )
            settings_obj.REDIS_URL = (
                f"{scheme}:{redis_key}@{redis_host}:{redis_port}/0"
            )

        # 4. Fetch SMS Notification Credentials
        sms_api_key = _secret("sms-provider-api-key")
        if sms_api_key:
            settings_obj.SMS_API_KEY = sms_api_key

        sms_account_sid = _secret("sms-provider-account-sid")
        if sms_account_sid:
            settings_obj.SMS_ACCOUNT_SID = sms_account_sid

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
