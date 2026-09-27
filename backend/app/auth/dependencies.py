from typing import Any, Dict, List

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt_validator import JWTValidationError, jwt_validator
from app.services.audit_service import audit_service

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> Dict[str, Any]:
    """
    Dependency that extracts the Bearer token, validates it against Microsoft Entra ID,
    and resolves the authenticated user profile and corporate role.
    """
    if not credentials or credentials.scheme.lower() != "bearer":
        audit_service.record_event(
            action="user_login",
            status="FAILED",
            details={"reason": "Missing or malformed Authorization header"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials are required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        claims = await jwt_validator.validate_token(token)

        # Resolve email from claims
        email = (
            claims.get("preferred_username") or claims.get("upn") or claims.get("email")
        )
        if not email:
            raise JWTValidationError("Missing email identifiers in token claims.")

        # Resolve name from claims
        name = claims.get("name") or email.split("@")[0]

        # Resolve roles list from claims
        raw_roles: List[str] = claims.get("roles", [])
        if isinstance(raw_roles, str):
            raw_roles = [raw_roles]

        # Map raw Entra ID roles to system roles
        role = "Standard User"
        if (
            "PlatformAdministrator" in raw_roles
            or "Platform Administrator" in raw_roles
            or "ITAdmin" in raw_roles
            or "IT Admin" in raw_roles
        ):
            role = "Platform Administrator"
        elif any(
            role_name in raw_roles
            for role_name in (
                "SupportEngineer",
                "Support Engineer",
                "SoftwareRequestApprover",
                "Approver",
                "Manager",
            )
        ):
            role = "Support Engineer"
        elif "Auditor" in raw_roles or "Auditor" in raw_roles:
            role = "Auditor"

        return {
            "email": email,
            "name": name,
            "role": role,
            "claims": claims,
        }
    except JWTValidationError as e:
        audit_service.record_event(
            action="user_login",
            status="FAILED",
            details={"reason": f"Token validation failed: {e.message}"},
        )
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )


def check_role(allowed_roles: List[str]):
    """
    FastAPI dependency factory that validates the current user possesses
    at least one of the allowed roles.
    """

    def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_role = current_user.get("role", "Standard User")
        if user_role not in allowed_roles:
            audit_service.record_event(
                action="dashboard_access",
                status="FAILED",
                details={
                    "email": current_user["email"],
                    "role": user_role,
                    "reason": f"Required roles: {allowed_roles}, possessed role: {user_role}",
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not possess the required privileges to view this resource.",
            )
        return current_user

    return role_checker
