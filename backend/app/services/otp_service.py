import secrets

from app.database.otp_repository import otp_repository

class OTPService:

    def generate_otp(self, email:str) -> str:

      """
      Generate a secure 6 digit OTP
      """

      otp = "".join(str(secrets.randbelow(10)) for _ in range(6))
      otp_repository.save_otp(email,otp)


      return otp

    def verify_otp(self, email: str, otp:str) -> bool:

        record = otp_repository.get_otp(email)

        if record is None:
          return False
        if record["otp"] != otp:
          return False

        otp_repository.delete_otp(email)


        return True





otp_service = OTPService()



