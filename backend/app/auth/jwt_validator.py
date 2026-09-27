import logging
import time
from typing import Any, Dict

import httpx
import jwt

from app.core.config import settings
from app.core.exceptions import BaseAppException

logger = logging.getLogger("itpa")


class JWTValidationError(BaseAppException):
    """Custom exception for JWT token validation errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 401,
        error_code: str = "JWT_VALIDATION_ERROR",
    ):
        super().__init__(message, status_code=status_code, error_code=error_code)


class JWTValidator:
    """
    Validates JWT tokens issued by Microsoft Entra ID (OIDC/MSAL).
    Supports local validation of HS256-signed mock tokens during local development.
    """

    def __init__(self) -> None:
        self.jwks_cache: Dict[str, Any] = {}
        self.jwks_expiry: float = 0.0

    @property
    def is_mock(self) -> bool:
        client_id = settings.ENTRA_CLIENT_ID or settings.CLIENT_ID
        tenant_id = settings.ENTRA_TENANT_ID or settings.TENANT_ID
        return not (client_id and tenant_id)

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Decodes, validates, and returns the claims from the JWT token.
        Raises JWTValidationError on signature mismatches, expiration, or invalid claims.
        """
        if not token:
            raise JWTValidationError("Authorization token is missing.")

        if self.is_mock:
            return await self._validate_mock_token(token)

        return await self._validate_entra_token(token)

    async def _validate_mock_token(self, token: str) -> Dict[str, Any]:
        """Decodes and validates a mock token signed using the local secret."""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=["HS256"],
                audience=settings.ENTRA_CLIENT_ID
                or settings.CLIENT_ID
                or "MOCK_CLIENT_ID",
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise JWTValidationError(
                "Session has expired. Please sign in again.", error_code="TOKEN_EXPIRED"
            )
        except jwt.InvalidTokenError:
            logger.warning("Mock JWT validation failed.")
            raise JWTValidationError("Invalid mock authorization token.")

    async def _validate_entra_token(self, token: str) -> Dict[str, Any]:
        """Downloads key metadata from Entra OIDC endpoint, decodes, and validates the token."""
        try:
            # Retrieve key ID (kid) from token header without validating signature first
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            if not kid:
                raise JWTValidationError(
                    "Invalid token structure: missing key ID header."
                )

            # Fetch matching public key from JWKS
            public_key = await self._get_public_key(kid)
            if not public_key:
                raise JWTValidationError(
                    "Unable to verify token signature: Unknown certificate key ID."
                )

            tenant_id = settings.ENTRA_TENANT_ID or settings.TENANT_ID
            client_id = settings.ENTRA_CLIENT_ID or settings.CLIENT_ID
            audience = settings.API_AUDIENCE or client_id

            # Define expected issuers (Entra ID supports both v2.0 and v1.0 token formats)
            issuers = [
                f"https://login.microsoftonline.com/{tenant_id}/v2.0",
                f"https://sts.windows.net/{tenant_id}/",
            ]
            if settings.AUTHORITY:
                authority = settings.AUTHORITY.rstrip("/")
                issuers.append(f"{authority}/v2.0")
                issuers.append(f"{authority}/")
                parts = authority.split("/")
                if len(parts) > 3:
                    t_id = parts[-1]
                    issuers.append(f"https://sts.windows.net/{t_id}/")

            # Decode and validate signature, issuer, audience, and expiration
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=audience,
                options={
                    "verify_signature": True,
                    "verify_aud": True,
                    "verify_iss": True,
                    "verify_exp": True,
                },
            )

            # Additional issuer check
            token_iss = payload.get("iss")
            if token_iss not in issuers:
                raise JWTValidationError(
                    f"Token issuer '{token_iss}' is not trusted for this corporate tenant."
                )

            return payload

        except jwt.ExpiredSignatureError:
            raise JWTValidationError(
                "Session has expired. Please sign in again.", error_code="TOKEN_EXPIRED"
            )
        except jwt.InvalidTokenError:
            logger.warning("OIDC JWT validation failed.")
            raise JWTValidationError("Invalid corporate access token.")
        except Exception as e:
            logger.error("Authentication check failed (%s).", type(e).__name__)
            raise JWTValidationError("Access token validation failed.")

    async def _get_public_key(self, kid: str) -> Any:
        """Retrieves corporate OIDC public keys, utilizing an in-memory cache with 12 hour expiry."""
        now = time.time()

        # Refresh cache if empty or expired
        if not self.jwks_cache or now > self.jwks_expiry:
            await self._refresh_jwks()

        key_data = self.jwks_cache.get(kid)
        if not key_data:
            # Re-fetch once in case of recent Microsoft key rotation
            await self._refresh_jwks()
            key_data = self.jwks_cache.get(kid)

        if not key_data:
            return None

        # Construct the PyJWT public key from JSON Web Key parameters
        return jwt.algorithms.RSAAlgorithm.from_jwk(key_data)

    async def _refresh_jwks(self) -> None:
        """Downloads key mapping from the Microsoft Entra ID OIDC discovery endpoint."""
        tenant_id = settings.ENTRA_TENANT_ID or settings.TENANT_ID
        # OIDC keys discovery URL
        jwks_url = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"

        logger.info("Fetching OIDC public keys from Microsoft...")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(jwks_url)
                response.raise_for_status()
                jwks = response.json()

                # Store keys indexed by their key ID (kid)
                new_cache = {}
                for key in jwks.get("keys", []):
                    if "kid" in key:
                        new_cache[key["kid"]] = key

                self.jwks_cache = new_cache
                # Set cache to expire in 12 hours
                self.jwks_expiry = time.time() + 43200
                logger.info(
                    "Successfully cached %d public keys from Entra ID.", len(new_cache)
                )
        except Exception as e:
            logger.error("Failed to fetch OIDC public keys (%s).", type(e).__name__)
            # Ensure we don't throw on network blips if cache already has data
            if not self.jwks_cache:
                raise JWTValidationError(
                    "Unable to retrieve public signing keys from identity provider.",
                    status_code=502,
                )


jwt_validator = JWTValidator()
