from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from app.models.user import User

class BaseAuthenticationProvider(ABC):
    """Base interface for all authentication providers."""

    @abstractmethod
    def verify_token(self, db: Session, token: str) -> User | None:
        """Verify the given token and return the associated local database User.
        
        Raises an exception or returns None if the token is invalid.
        """
        pass
