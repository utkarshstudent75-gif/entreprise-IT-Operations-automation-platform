from datetime import datetime, timedelta


class OTPRepository:
    def __init__(self):
        self._otp_store = {}

    def save_otp(self, email: str, otp: str, expiry_minutes: int = 5):

        self._otp_store[email] = {
            "otp": otp,
            "expires_at": datetime.utcnow() + timedelta(minutes=expiry_minutes),
            "attempts": 0,
        }

    def get_otp(self, email: str):

        return self._otp_store.get(email)

    def delete_otp(self, email: str):

        self._otp_store.pop(email, None)


otp_repository = OTPRepository()
