from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """Database access for user records."""

    def get_by_username(self, db: Session, username: str) -> User | None:
        return db.query(User).filter(User.username == username).one_or_none()

    def get_by_email(self, db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).one_or_none()

    def get_by_id(self, db: Session, user_id: int) -> User | None:
        return db.query(User).filter(User.id == user_id).one_or_none()

    def create_user(
        self,
        db: Session,
        username: str,
        email: str,
        hashed_password: str,
    ) -> User:
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


user_repository = UserRepository()
