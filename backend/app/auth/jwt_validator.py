import jwt
from fastapi import status
from jwt import PyJWKClient

from app.core.config import settings
from app.core.exceptions import BaseAppException


class EntraJWTValidator:
    """Validator for Microsoft Entra ID JWT tokens using JWKS."""

    def __init__(self):
        # The common keys endpoint works for verifying tokens from all tenants
        self.jwks_url = "https://login.microsoftonline.com/common/discovery/v2.0/keys"
        self.jwks_client = PyJWKClient(self.jwks_url)

    def validate_token(self, token: str) -> dict:
        """Decode and validate a Microsoft Entra ID token.

        Returns the decoded token claims if valid, raises an exception otherwise.
        """
        try:
            # 1. Unverified decode to extract tenant ID and claims for issuer validation
            unverified_claims = jwt.decode(token, options={"verify_signature": False})
        except jwt.PyJWTError as e:
            raise BaseAppException(
                f"Invalid token format: {str(e)}",
                status_code=status.HTTP_401_UNAUTHORIZED,
                error_code="INVALID_TOKEN",
            )

        tenant_id = unverified_claims.get("tid")
        if not tenant_id:
            raise BaseAppException(
                "Missing tenant ID (tid) claim in token.",
                status_code=status.HTTP_401_UNAUTHORIZED,
                error_code="INVALID_TOKEN",
            )

        # Tenant Lock Check: If ENTRA_TENANT_ID is configured and not "common",
        # ensure the token's tenant matches the configured tenant.
        configured_tenant = settings.ENTRA_TENANT_ID
        if configured_tenant and configured_tenant != "common":
            if tenant_id != configured_tenant:
                raise BaseAppException(
                    f"Tenant ID mismatch. Expected {configured_tenant}, got {tenant_id}.",
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    error_code="INVALID_ISSUER",
                )

        # 2. Get signing key from JWKS client
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
        except Exception as e:
            raise BaseAppException(
                f"Failed to retrieve signing key: {str(e)}",
                status_code=status.HTTP_401_UNAUTHORIZED,
                error_code="INVALID_SIGNATURE",
            )

        # 3. Define allowed issuers
        allowed_issuers = [
            f"https://login.microsoftonline.com/{tenant_id}/v2.0",
            f"https://sts.windows.net/{tenant_id}/",
        ]

        # 4. Decode and verify signature, audience, expiration
        try:
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=settings.ENTRA_CLIENT_ID,
                options={"verify_exp": True, "verify_iss": True, "verify_aud": True},
            )

            # Additional check: verify issuer matches one of the allowed issuers
            iss = claims.get("iss")
            if iss not in allowed_issuers:
                raise jwt.InvalidIssuerError(f"Issuer {iss} not in allowed issuers.")

            return claims

        except jwt.ExpiredSignatureError:
            raise BaseAppException(
                "Token has expired.",
                status_code=status.HTTP_401_UNAUTHORIZED,
                error_code="TOKEN_EXPIRED",
            )
        except jwt.InvalidIssuerError as e:
            raise BaseAppException(
                f"Token issuer validation failed: {str(e)}",
                status_code=status.HTTP_401_UNAUTHORIZED,
                error_code="INVALID_ISSUER",
            )
        except jwt.InvalidAudienceError as e:
            raise BaseAppException(
                f"Token audience mismatch: {str(e)}",
                status_code=status.HTTP_401_UNAUTHORIZED,
                error_code="INVALID_AUDIENCE",
            )
        except jwt.PyJWTError as e:
            raise BaseAppException(
                f"Token verification failed: {str(e)}",
                status_code=status.HTTP_401_UNAUTHORIZED,
                error_code="INVALID_TOKEN",
            )
