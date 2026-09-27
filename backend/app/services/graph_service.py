import asyncio
import logging
import time
from typing import Optional
from urllib.parse import quote

import httpx

from app.core.config import settings
from app.core.exceptions import BaseAppException
from app.core.redis import get_redis

logger = logging.getLogger("itpa")


class GraphAPIException(BaseAppException):
    """Custom exception for MS Graph API integrations."""

    def __init__(
        self, message: str, status_code: int = 400, error_code: str = "GRAPH_API_ERROR"
    ):
        super().__init__(message, status_code=status_code, error_code=error_code)


class GraphService:
    """
    Service interfacing with Microsoft Graph API using application permissions.
    Supports automatic fallback to mock mode for local testing if credentials are unset.
    """

    def __init__(self) -> None:
        self._in_memory_token: Optional[str] = None
        self._in_memory_expiry: float = 0.0

    @property
    def is_mock(self) -> bool:
        client_id = settings.ENTRA_CLIENT_ID or settings.CLIENT_ID
        tenant_id = settings.ENTRA_TENANT_ID or settings.TENANT_ID
        return not (client_id and tenant_id)

    async def get_access_token(self) -> str:
        """
        Acquires and returns a valid Graph API access token.
        Uses Redis caching with automatic renewal, falling back to in-memory cache if needed.
        """
        if self.is_mock:
            return "MOCK_GRAPH_ACCESS_TOKEN"

        now = time.time()

        # 1. Try retrieving token from Redis cache
        try:
            redis_client = await get_redis()
            cached_token = await redis_client.get("entra:access_token")
            if cached_token:
                # Check TTL on key
                ttl = await redis_client.ttl("entra:access_token")
                # Renew if within 5 minutes (300 seconds) of expiration
                if ttl > 300:
                    return cached_token.decode("utf-8")
        except Exception as e:
            logger.warning(
                "Redis access token retrieval failed (%s); falling back to memory.",
                type(e).__name__,
            )

        # 2. Try retrieving from in-memory cache
        if self._in_memory_token and (self._in_memory_expiry - now > 300):
            return self._in_memory_token

        # 3. Cache miss: acquire new token from Microsoft Entra ID
        token = await self._acquire_token_from_entra()

        # Cache token in memory
        self._in_memory_token = token
        self._in_memory_expiry = now + 3500  # standard token lifetime is 3600s

        # Cache token in Redis
        try:
            redis_client = await get_redis()
            # Set key to expire in 3500 seconds
            await redis_client.set("entra:access_token", token, ex=3500)
        except Exception as e:
            logger.warning(
                "Failed to store access token in Redis (%s).", type(e).__name__
            )

        return token

    async def _acquire_token_from_entra(self) -> str:
        """Sends token request using configured client secret or Managed Identity."""
        logger.info("Requesting new access token from Microsoft Entra ID...")

        # HTTP client timeout parameters
        timeout = httpx.Timeout(10.0, connect=5.0)

        if settings.USE_MANAGED_IDENTITY:
            # Obtain token via Azure Instance Metadata Service (IMDS)
            imds_url = "http://169.254.169.254/metadata/identity/oauth2/token"
            params = {
                "api-version": "2018-02-01",
                "resource": "https://graph.microsoft.com",
            }
            headers = {"Metadata": "true"}

            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(
                        imds_url, params=params, headers=headers
                    )
                    response.raise_for_status()
                    data = response.json()
                    return data["access_token"]
            except Exception as e:
                logger.error(
                    "Managed Identity token acquisition failed (%s).",
                    type(e).__name__,
                )
                raise GraphAPIException(
                    "Failed to acquire token from Managed Identity service.",
                    status_code=502,
                )
        else:
            # Obtain token via Client Credentials Flow
            tenant_id = settings.ENTRA_TENANT_ID or settings.TENANT_ID
            client_id = settings.ENTRA_CLIENT_ID or settings.CLIENT_ID
            client_secret = settings.ENTRA_CLIENT_SECRET or settings.CLIENT_SECRET
            scope = settings.GRAPH_SCOPES or "https://graph.microsoft.com/.default"

            token_url = (
                f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
            )
            payload = {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": scope,
            }

            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(token_url, data=payload)
                    response.raise_for_status()
                    data = response.json()
                    return data["access_token"]
            except Exception as e:
                logger.error("Client credentials flow failed (%s).", type(e).__name__)
                raise GraphAPIException(
                    "Authentication failed: Unable to connect to Microsoft Entra ID.",
                    status_code=502,
                )

    async def lookup_user(self, email: str) -> bool:
        """
        Check if a user exists in Microsoft Entra ID.
        Returns True if user exists, False if not.
        """
        if self.is_mock:
            logger.info("[Mock Mode] Looking up user in Entra ID.")
            email_lower = email.lower()
            if any(
                prefix in email_lower
                for prefix in [
                    "unknown",
                    "missing",
                    "stranger",
                    "notfound",
                    "nonexistent",
                ]
            ):
                return False
            # Simulating that any corporate domain email exists
            if (
                "@example.com" in email_lower
                or "@enterprise.com" in email_lower
                or "riya" in email_lower
                or "arsh" in email_lower
                or "alex.morgan" in email_lower
                or "morgan" in email_lower
            ):
                return True
            return False

        token = await self.get_access_token()
        url = f"{settings.GRAPH_ENDPOINT}/users/{email}"
        headers = {"Authorization": f"Bearer {token}"}

        # Retry logic configuration
        attempts = 3
        for attempt in range(attempts):
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(url, headers=headers)

                    if response.status_code == 200:
                        return True
                    if response.status_code == 404:
                        return False

                    # Trigger retry for transient status codes
                    if response.status_code in (429, 502, 503, 504):
                        if attempt < attempts - 1:
                            await asyncio.sleep(0.5 * (2**attempt))
                            continue

                    response.raise_for_status()
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                if attempt < attempts - 1:
                    await asyncio.sleep(0.5 * (2**attempt))
                    continue
                logger.error("Graph API user lookup failed (%s).", type(e).__name__)
                raise GraphAPIException(
                    "Network connection error to Microsoft Graph API.", status_code=504
                )
            except httpx.HTTPStatusError:
                logger.error(
                    "Graph API user lookup returned HTTP %d.", response.status_code
                )
                raise GraphAPIException(
                    f"Graph query returned status {response.status_code}.",
                    status_code=500,
                )

        return False

    async def reset_password(self, email: str, new_password: str) -> None:
        """
        Resets the password profile of the specified user in Microsoft Entra ID.
        Translates OData error messages into user-friendly security alerts.
        """
        if self.is_mock:
            logger.info("[Mock Mode] Password reset requested via Microsoft Graph.")
            if "violation" in new_password.lower():
                raise GraphAPIException(
                    "The password does not meet corporate complexity requirements.",
                    status_code=400,
                    error_code="PASSWORD_POLICY_VIOLATION",
                )
            if "disabled" in email:
                raise GraphAPIException(
                    "This account is currently disabled.",
                    status_code=400,
                    error_code="ACCOUNT_DISABLED",
                )
            if "locked" in email:
                raise GraphAPIException(
                    "This account is currently locked.",
                    status_code=400,
                    error_code="ACCOUNT_LOCKED",
                )
            return

        token = await self.get_access_token()
        url = f"{settings.GRAPH_ENDPOINT}/users/{email}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload = {
            "passwordProfile": {
                "forceChangePasswordNextSignIn": settings.PASSWORD_FORCE_CHANGE_ON_NEXT_SIGNIN,
                "password": new_password,
            }
        }

        attempts = 3
        for attempt in range(attempts):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.patch(url, json=payload, headers=headers)

                    if response.status_code == 204:
                        logger.info("Password updated successfully via Graph API.")
                        return

                    # Trigger retry for transient status codes
                    if response.status_code in (429, 502, 503, 504):
                        if attempt < attempts - 1:
                            await asyncio.sleep(0.5 * (2**attempt))
                            continue

                    # Process specific errors
                    response_data = response.json()
                    error_details = response_data.get("error", {})
                    error_code = error_details.get("code", "")
                    error_msg = error_details.get("message", "")

                    logger.error(
                        "Microsoft Graph password reset failed with HTTP %d.",
                        response.status_code,
                    )

                    # Map OData errors to specific business rules
                    if (
                        error_code == "Authorization_RequestDenied"
                        or "insufficient privileges" in error_msg.lower()
                    ):
                        raise GraphAPIException(
                            "Insufficient permissions to reset this account's password. Administrative accounts cannot be reset by application-level permissions.",
                            status_code=403,
                            error_code="INSUFFICIENT_PERMISSIONS",
                        )
                    elif (
                        "password policy" in error_msg.lower()
                        or "complexity" in error_msg.lower()
                    ):
                        raise GraphAPIException(
                            "The password does not meet corporate complexity requirements.",
                            status_code=400,
                            error_code="PASSWORD_POLICY_VIOLATION",
                        )
                    elif "disabled" in error_msg.lower():
                        raise GraphAPIException(
                            "This account is currently disabled.",
                            status_code=400,
                            error_code="ACCOUNT_DISABLED",
                        )
                    elif "locked" in error_msg.lower():
                        raise GraphAPIException(
                            "This account is currently locked.",
                            status_code=400,
                            error_code="ACCOUNT_LOCKED",
                        )
                    else:
                        raise GraphAPIException(
                            f"Graph password reset failed: {error_msg}",
                            status_code=response.status_code,
                        )

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                if attempt < attempts - 1:
                    await asyncio.sleep(0.5 * (2**attempt))
                    continue
                logger.error("Graph API password reset failed (%s).", type(e).__name__)
                raise GraphAPIException(
                    "Network connection error to Microsoft Graph API.", status_code=504
                )
            except GraphAPIException:
                raise
            except Exception as e:
                logger.error(
                    "Unexpected Graph password reset error (%s).", type(e).__name__
                )
                raise GraphAPIException(
                    "An unexpected error occurred while resetting the password.",
                    status_code=500,
                )

    async def reset_mfa_methods(self, email: str) -> int:
        """Remove supported non-password authentication methods for one user."""
        if self.is_mock:
            logger.info("[Mock Mode] MFA reset requested via Microsoft Graph.")
            return 1

        token = await self.get_access_token()
        encoded_email = quote(email, safe="")
        url = f"{settings.GRAPH_ENDPOINT}/users/{encoded_email}/authentication/methods"
        headers = {"Authorization": f"Bearer {token}"}
        deletable_methods = {
            "#microsoft.graph.emailAuthenticationMethod": "emailMethods",
            "#microsoft.graph.externalAuthenticationMethod": "externalAuthenticationMethods",
            "#microsoft.graph.fido2AuthenticationMethod": "fido2Methods",
            "#microsoft.graph.microsoftAuthenticatorAuthenticationMethod": "microsoftAuthenticatorMethods",
            "#microsoft.graph.phoneAuthenticationMethod": "phoneMethods",
            "#microsoft.graph.platformCredentialAuthenticationMethod": "platformCredentialMethods",
            "#microsoft.graph.softwareOathAuthenticationMethod": "softwareOathMethods",
            "#microsoft.graph.temporaryAccessPassAuthenticationMethod": "temporaryAccessPassMethods",
            "#microsoft.graph.windowsHelloForBusinessAuthenticationMethod": "windowsHelloForBusinessMethods",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    logger.error(
                        "Graph MFA methods lookup returned HTTP %d.",
                        response.status_code,
                    )
                    raise GraphAPIException(
                        "Unable to reset authentication methods for this account.",
                        status_code=502,
                    )

                try:
                    result = response.json()
                except ValueError as exc:
                    raise GraphAPIException(
                        "Microsoft Graph returned an invalid response.",
                        status_code=502,
                    ) from exc

                methods = result.get("value") if isinstance(result, dict) else None
                if not isinstance(methods, list):
                    raise GraphAPIException(
                        "Microsoft Graph returned an invalid response.",
                        status_code=502,
                    )

                deletions: list[tuple[str, str]] = []
                for method in methods:
                    if not isinstance(method, dict):
                        raise GraphAPIException(
                            "Microsoft Graph returned an invalid response.",
                            status_code=502,
                        )
                    method_type = method.get("@odata.type")
                    if method_type == "#microsoft.graph.passwordAuthenticationMethod":
                        continue
                    if not isinstance(method_type, str):
                        raise GraphAPIException(
                            "Microsoft Graph returned an invalid authentication method.",
                            status_code=502,
                        )
                    collection = deletable_methods.get(method_type)
                    method_id = method.get("id")
                    if (
                        not collection
                        or not isinstance(method_id, str)
                        or not method_id
                    ):
                        raise GraphAPIException(
                            "The account has an authentication method this service cannot reset.",
                            status_code=502,
                        )
                    deletions.append((collection, quote(method_id, safe="")))

                for collection, method_id in deletions:
                    delete_url = (
                        f"{settings.GRAPH_ENDPOINT}/users/{encoded_email}"
                        f"/authentication/{collection}/{method_id}"
                    )
                    delete_response = await client.delete(delete_url, headers=headers)
                    if delete_response.status_code not in (200, 202, 204, 404):
                        logger.error(
                            "Graph MFA method deletion returned HTTP %d.",
                            delete_response.status_code,
                        )
                        raise GraphAPIException(
                            "Unable to reset authentication methods for this account.",
                            status_code=502,
                        )

                return len(deletions)
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            logger.error("Graph MFA reset failed (%s).", type(exc).__name__)
            raise GraphAPIException(
                "Microsoft Graph could not process the authentication reset.",
                status_code=504,
            ) from exc

    async def get_user_phone(self, email: str) -> str | None:
        """
        Retrieves the business phone number (or mobile phone number) for a user from Microsoft Graph.
        """
        if self.is_mock:
            logger.info("[Mock Mode] Fetching user phone number.")
            # Default mock values for local test accounts
            if "alex.morgan" in email.lower() or "morgan" in email.lower():
                return "+911800123456"
            return None

        token = await self.get_access_token()
        url = f"{settings.GRAPH_ENDPOINT}/users/{email}?$select=businessPhones,mobilePhone"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    # businessPhones takes precedence for Entra ID business phone number
                    business = data.get("businessPhones", [])
                    if business and len(business) > 0:
                        return business[0]

                    mobile = data.get("mobilePhone")
                    if mobile:
                        return mobile
        except Exception as e:
            logger.warning(
                "Failed to fetch user phone from Graph API (%s).", type(e).__name__
            )

        return None


graph_service = GraphService()
