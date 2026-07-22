from datetime import datetime, UTC
from sqlalchemy.orm import Session
from app.models.user import User
from app.auth.providers.base import BaseAuthenticationProvider
from app.auth.jwt_validator import EntraJWTValidator
from app.core.exceptions import BaseAppException
from fastapi import status

class EntraAuthenticationProvider(BaseAuthenticationProvider):
    """Microsoft Entra ID authentication provider."""

    def __init__(self):
        self.validator = EntraJWTValidator()

    def verify_token(self, db: Session, token: str) -> User | None:
        # Validate token and extract claims
        claims = self.validator.validate_token(token)
        
        oid = claims.get("oid") or claims.get("sub")
        if not oid:
            raise BaseAppException(
                "Token is missing object identifier (oid/sub) claim.",
                status_code=status.HTTP_401_UNAUTHORIZED,
                error_code="INVALID_TOKEN",
            )
            
        email = claims.get("email") or claims.get("preferred_username") or claims.get("unique_name")
        if not email:
            raise BaseAppException(
                "Token is missing email claim.",
                status_code=status.HTTP_401_UNAUTHORIZED,
                error_code="INVALID_TOKEN",
            )
            
        display_name = claims.get("name") or email.split("@")[0]
        tenant_id = claims.get("tid")
        
        # User Mapping
        # 1. Try to query by entra_oid
        user = db.query(User).filter(User.entra_oid == oid).one_or_none()
        
        # 2. If not found, look up by email to link existing account
        if not user:
            user = db.query(User).filter(User.email == email).one_or_none()
            
        now_utc = datetime.now(UTC).replace(tzinfo=None)
        
        if user:
            # Update user details
            user.entra_oid = oid
            user.display_name = display_name
            user.entra_tenant_id = tenant_id
            user.last_login = now_utc
            # Ensure email matches just in case it updated in Entra ID
            user.email = email
            db.commit()
            db.refresh(user)
        else:
            # Create user
            user = User(
                username=email,
                email=email,
                hashed_password=None,
                entra_oid=oid,
                display_name=display_name,
                entra_tenant_id=tenant_id,
                last_login=now_utc,
                roles="HelpDesk", # Default role
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
        return user
