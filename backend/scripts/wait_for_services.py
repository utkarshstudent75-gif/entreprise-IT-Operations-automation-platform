import asyncio
import sys

from sqlalchemy import text

from app.core.redis import redis_manager
from app.database.session import SessionLocal


def check_postgres() -> bool:
    print("Checking PostgreSQL connection...")
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        print("✓ PostgreSQL is reachable.")
        return True
    except Exception as e:
        print(f"✗ PostgreSQL connection failed: {e}", file=sys.stderr)
        return False
    finally:
        db.close()


async def check_redis() -> bool:
    print("Checking Redis connection...")
    try:
        redis_manager.init_redis()
        ping_ok = await redis_manager.ping()
        if ping_ok:
            print("✓ Redis is reachable.")
            return True
        else:
            print("✗ Redis ping failed.", file=sys.stderr)
            return False
    except Exception as e:
        print(f"✗ Redis connection failed: {e}", file=sys.stderr)
        return False
    finally:
        await redis_manager.close()


async def main():
    pg_ok = check_postgres()
    redis_ok = await check_redis()

    if not pg_ok or not redis_ok:
        print(
            "Critical service dependencies are unavailable. Exiting.", file=sys.stderr
        )
        sys.exit(1)
    print("All backend services are ready.")


if __name__ == "__main__":
    asyncio.run(main())
