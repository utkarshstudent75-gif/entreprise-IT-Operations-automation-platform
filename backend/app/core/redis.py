import logging

from redis.asyncio import ConnectionPool, Redis

from app.core.config import settings

logger = logging.getLogger("itpa")


class RedisManager:
    def __init__(self):
        self.pool: ConnectionPool | None = None
        self.client: Redis | None = None

    def init_redis(self) -> None:
        """
        Initialize the connection pool and client.
        """
        if self.client is not None:
            return

        if settings.REDIS_URL:
            url = settings.REDIS_URL
        else:
            password_part = (
                f":{settings.REDIS_PASSWORD}@" if settings.REDIS_PASSWORD else ""
            )
            url = f"redis://{password_part}{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"

        self.pool = ConnectionPool.from_url(
            url, decode_responses=True, retry_on_timeout=True, health_check_interval=30
        )
        self.client = Redis(connection_pool=self.pool)

    async def ping(self) -> bool:
        """
        Ping Redis to check connectivity.
        """
        if not self.client:
            return False
        try:
            await self.client.ping()
            return True
        except Exception:
            return False

    async def check_health_and_reconnect(self) -> bool:
        """
        Check health of the current connection. If failed, attempt reconnect safely.
        """
        if await self.ping():
            return True

        logger.info("Reconnect Attempt")
        try:
            await self.close()
        except Exception as e:
            logger.debug("Failed to close Redis connection: %s", e)

        self.init_redis()

        if await self.ping():
            logger.info("Redis Connected")
            return True
        else:
            logger.error("Connection Failed")
            return False

    async def close(self) -> None:
        """
        Close client and connection pool.
        """
        if self.client:
            await self.client.close()
        if self.pool:
            await self.pool.disconnect()
            logger.info("Redis Disconnected")
        self.client = None
        self.pool = None


redis_manager = RedisManager()


async def get_redis() -> Redis:
    if redis_manager.client is None:
        redis_manager.init_redis()
    return redis_manager.client
