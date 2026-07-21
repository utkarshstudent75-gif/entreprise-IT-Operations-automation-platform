# ruff: noqa: E402
import os
import sys

# Add the parent directory to sys.path to resolve 'app' imports correctly
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from app.core.exceptions import DuplicateUserException
from app.database.session import SessionLocal
from app.schemas.user import UserCreate
from app.services.user_service import user_service


def seed_users():
    """Seed test users into the database using the project's service layer."""
    db = SessionLocal()
    users_to_create = [
        {"username": "riya", "email": "riya@example.com", "password": "Password123!"},
        {"username": "arsh", "email": "arsh@example.com", "password": "Password123!"},
    ]

    print("Starting database seeding...")
    try:
        for user_data in users_to_create:
            request = UserCreate(
                username=user_data["username"],
                email=user_data["email"],
                password=user_data["password"],
            )
            try:
                # Create the user using the project's user service (hashes passwords, performs validations)
                user = user_service.create_user(db, request)
                db.commit()
                print(
                    f"✔ Successfully created user: {user.username} ({user.email}) [ID: {user.id}]"
                )
            except DuplicateUserException:
                db.rollback()
                print(f"ℹ User '{user_data['username']}' already exists, skipping.")
            except Exception as e:
                db.rollback()
                print(f"❌ Error creating user '{user_data['username']}': {e}")
    finally:
        db.close()
    print("Database seeding completed.")


if __name__ == "__main__":
    seed_users()
