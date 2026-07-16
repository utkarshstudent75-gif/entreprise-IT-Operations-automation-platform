from datetime import UTC, datetime, timedelta


class OTPRepository:
    def __init__(self):
        self._otp_store = {}

    def save_otp(self, email: str, otp: str, expiry_minutes: int = 5):

        self._otp_store[email] = {
            "otp": otp,
            "expires_at": datetime.now(UTC) + timedelta(minutes=expiry_minutes),
            "attempts": 0,
        }

    def get_otp(self, email: str):

        return self._otp_store.get(email)

    def delete_otp(self, email: str):

        self._otp_store.pop(email, None)

    def increment_attempts(self, email: str) -> int:
        """Increment and return the number of failed verification attempts."""
        record = self._otp_store.get(email)
        if record is None:
            return 0

        record["attempts"] += 1
        return record["attempts"]


otp_repository = OTPRepository()
