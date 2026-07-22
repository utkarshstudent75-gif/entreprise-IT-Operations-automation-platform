from app.core.config import settings
from app.auth.providers.base import BaseAuthenticationProvider
from app.auth.providers.local import LocalAuthenticationProvider
from app.auth.providers.entra import EntraAuthenticationProvider

def get_auth_provider() -> BaseAuthenticationProvider:
    provider_name = settings.AUTH_PROVIDER.lower() if settings.AUTH_PROVIDER else "local"
    if provider_name == "entra":
        return EntraAuthenticationProvider()
    else:
        return LocalAuthenticationProvider()

auth_service = get_auth_provider()
