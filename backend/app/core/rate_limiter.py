import abc
import threading
import time

from app.core.exceptions import RateLimitExceededException


class RateLimiterStorage(abc.ABC):
    """
    Abstract Base Class for Rate Limiter Storage.
    Allows changing from in-memory to Redis/other store without modifying the API logic.
    """

    @abc.abstractmethod
    def is_rate_limited(self, key: str, limit: int, window_seconds: int) -> bool:
        """
        Determine if the request for the given key is rate limited.
        Increments the request count and returns True if limit is exceeded,
        False otherwise.
        """
        pass


class InMemoryRateLimiterStorage(RateLimiterStorage):
    """
    Thread-safe In-Memory implementation of Rate Limiter Storage using
    sliding window log.
    """

    def __init__(self):
        self._requests = {}
        self._lock = threading.Lock()

    def is_rate_limited(self, key: str, limit: int, window_seconds: int) -> bool:
        with self._lock:
            now = time.time()
            cutoff = now - window_seconds

            # Retrieve existing timestamps and filter out those older than cutoff
            timestamps = self._requests.get(key, [])
            timestamps = [ts for ts in timestamps if ts > cutoff]

            if len(timestamps) >= limit:
                # Store the updated list (prevent memory leak of old entries)
                self._requests[key] = timestamps
                return True

            # Register the new attempt
            timestamps.append(now)
            self._requests[key] = timestamps
            return False


class RateLimiter:
    """
    RateLimiter class coordinating limits validation with storage layer.
    """

    def __init__(self, storage: RateLimiterStorage):
        self.storage = storage

    def check_limit(self, key: str, limit: int, window_seconds: int) -> None:
        """
        Verifies if rate limit is exceeded for the key.
        Raises RateLimitExceededException if limited.
        """
        if self.storage.is_rate_limited(key, limit, window_seconds):
            raise RateLimitExceededException()


# Global rate limiter instance using the thread-safe in-memory store
rate_limiter = RateLimiter(InMemoryRateLimiterStorage())
