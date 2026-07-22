import hashlib
import logging

from redis.asyncio import Redis

from app.core.redis import get_redis

logger = logging.getLogger("itpa")


class RedisService:
    """
    Central service for managing OTP lifecycle and retry attempts in Redis.
    """

    def generate_key(self, email: str) -> str:
        return f"otp:{email}"

    def _get_key(self, email: str) -> str:
        return self.generate_key(email)

    def _get_meta_key(self, email: str) -> str:
        return f"otp:meta:{email}"

    def _get_used_key(self, email: str) -> str:
        return f"otp:used:{email}"

    def _hash_otp(self, otp: str) -> str:
        return hashlib.sha256(otp.encode("utf-8")).hexdigest()

    async def store_otp(self, email: str, otp: str, expires_in_seconds: int) -> None:
        """
        Store the hashed OTP in Redis.
        Also writes a meta key with a longer expiry to distinguish between
        expired OTPs and invalid requests.
        """
        client: Redis = await get_redis()
        key = self._get_key(email)
        meta_key = self._get_meta_key(email)
        otp_hash = self._hash_otp(otp)

        # Store otp hash and reset attempts
        await client.hset(key, mapping={"otp_hash": otp_hash, "attempts": "0"})
        await client.expire(key, int(expires_in_seconds))

        # Meta key persists longer to track that an OTP was indeed generated
        await client.set(meta_key, "1", ex=int(expires_in_seconds) * 24)

        logger.info("OTP stored for email: %s", email)

    async def get_otp(self, email: str) -> dict | None:
        """
        Retrieve the OTP data (otp_hash and attempts) for the given email.
        """
        client: Redis = await get_redis()
        key = self._get_key(email)
        data = await client.hgetall(key)
        if not data:
            return None
        return data

    async def increment_attempts(self, email: str) -> int:
        """
        Increment the verification attempts counter for the OTP.
        """
        client: Redis = await get_redis()
        key = self._get_key(email)
        return await client.hincrby(key, "attempts", 1)

    async def clear_attempts(self, email: str) -> None:
        """
        Reset the attempts counter for the OTP.
        """
        client: Redis = await get_redis()
        key = self._get_key(email)
        await client.hset(key, "attempts", "0")

    async def delete_otp(self, email: str) -> None:
        """
        Delete the OTP and its associated metadata from Redis.
        """
        client: Redis = await get_redis()
        await client.delete(self._get_key(email))
        await client.delete(self._get_meta_key(email))
        logger.info("OTP deleted for email: %s", email)

    async def verify_otp(
        self,
        email: str,
        otp: str,
        consume: bool = False,
        max_attempts: int = 3,
        expires_in_seconds: int = 300,
    ) -> bool:
        """
        Perform secure OTP verification.
        - Checks if OTP has already been used.
        - Checks if OTP exists.
        - If OTP doesn't exist, checks metadata to see if it expired or was never requested.
        - Enforces max attempts logic.
        - Compares hashes securely.
        - If consume is True, deletes the active OTP and registers it as used.
        """
        from app.core.exceptions import (
            ExpiredOTPException,
            InvalidOTPException,
            OTPAlreadyUsedException,
        )

        otp_hash = self._hash_otp(otp)

        # 1. Check if OTP was already used
        client: Redis = await get_redis()
        used_key = self._get_used_key(email)
        used_val = await client.get(used_key)
        if used_val == otp_hash:
            raise OTPAlreadyUsedException("OTP has already been used.")

        # 2. Check if active OTP exists
        data = await self.get_otp(email)
        if not data:
            # Check if it expired or was never requested
            meta_exists = await client.exists(self._get_meta_key(email))
            if meta_exists:
                raise ExpiredOTPException("OTP has expired.")
            raise InvalidOTPException("Invalid email or OTP.")

        stored_hash = data.get("otp_hash")
        attempts = int(data.get("attempts", 0))

        # 3. Check if attempts already exceeded before comparison
        if attempts >= max_attempts:
            await self.delete_otp(email)
            raise InvalidOTPException("Invalid email or OTP.")

        # 4. Compare securely
        import secrets

        if not secrets.compare_digest(stored_hash, otp_hash):
            # Increment attempts on failure
            attempts = await self.increment_attempts(email)
            if attempts >= max_attempts:
                await self.delete_otp(email)
            raise InvalidOTPException("Invalid email or OTP.")

        # 5. Success
        if consume:
            await self.delete_otp(email)
            # Mark OTP as used to prevent replay attacks within the expiry window
            await client.set(used_key, otp_hash, ex=expires_in_seconds)

        return True


redis_service = RedisService()
