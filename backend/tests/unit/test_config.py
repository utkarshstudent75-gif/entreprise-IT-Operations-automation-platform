from unittest.mock import MagicMock, patch

from app.core.config import Settings, retrieve_secrets_from_key_vault


def test_config_alternate_mapping():
    settings = Settings(
        TENANT_ID="test-tenant",
        CLIENT_ID="test-client",
        CLIENT_SECRET="test-secret",
        GRAPH_SCOPES="https://graph.microsoft.com/.default",
        DATABASE_URL="postgresql://postgres:postgres@postgres:5432/eitoap",
    )
    # Check manual alignment
    if settings.TENANT_ID and not settings.ENTRA_TENANT_ID:
        settings.ENTRA_TENANT_ID = settings.TENANT_ID
    if settings.CLIENT_ID and not settings.ENTRA_CLIENT_ID:
        settings.ENTRA_CLIENT_ID = settings.CLIENT_ID
    if settings.CLIENT_SECRET and not settings.ENTRA_CLIENT_SECRET:
        settings.ENTRA_CLIENT_SECRET = settings.CLIENT_SECRET

    assert settings.ENTRA_TENANT_ID == "test-tenant"
    assert settings.ENTRA_CLIENT_ID == "test-client"
    assert settings.ENTRA_CLIENT_SECRET == "test-secret"
    assert settings.GRAPH_SCOPES == "https://graph.microsoft.com/.default"


def test_retrieve_secrets_from_key_vault():
    settings = Settings(
        KEYVAULT_NAME="mytestvault",
        DATABASE_URL="postgresql://postgres:postgres@postgres:5432/eitoap",
    )

    # Mock Azure Key Vault clients
    mock_secret_client = MagicMock()

    mock_secrets = {
        "msgraph-client-id": MagicMock(value="kv-client-id"),
        "msgraph-client-secret": MagicMock(value="kv-client-secret"),
        "msgraph-tenant-id": MagicMock(value="kv-tenant-id"),
        "database-host": MagicMock(value="kv-db-host"),
        "database-name": MagicMock(value="kv-db-name"),
        "database-port": MagicMock(value="5432"),
        "database-username": MagicMock(value="kv-db-user"),
        "database-password": MagicMock(value="kv-db-pass"),
        "redis-host": MagicMock(value="kv-redis-host"),
        "redis-port": MagicMock(value="6379"),
        "redis-primary-key": MagicMock(value="kv-redis-key"),
        "sms-provider-api-key": MagicMock(value="kv-sms-key"),
        "sms-provider-account-sid": MagicMock(value="kv-sms-sid"),
    }

    mock_secret_client.get_secret.side_effect = lambda name: mock_secrets.get(name)

    with patch(
        "azure.keyvault.secrets.SecretClient", return_value=mock_secret_client
    ), patch("azure.identity.DefaultAzureCredential", return_value=MagicMock()):

        retrieve_secrets_from_key_vault(settings)

        assert settings.CLIENT_ID == "kv-client-id"
        assert settings.CLIENT_SECRET == "kv-client-secret"
        assert settings.TENANT_ID == "kv-tenant-id"
        assert settings.ENTRA_CLIENT_ID == "kv-client-id"
        assert (
            settings.DATABASE_URL
            == "postgresql://kv-db-user:kv-db-pass@kv-db-host:5432/kv-db-name"
        )
        assert settings.REDIS_HOST == "kv-redis-host"
        assert settings.REDIS_PORT == 6379
        assert settings.REDIS_PASSWORD == "kv-redis-key"
        assert settings.REDIS_URL == "redis://:kv-redis-key@kv-redis-host:6379/0"
        assert settings.SMS_API_KEY == "kv-sms-key"
        assert settings.SMS_ACCOUNT_SID == "kv-sms-sid"
