import secrets


class OTPService:

  def generate_otp(self) -> str:

      """

      Generate a secure 6 digit OTP


      """

    otp = "".join(str(secrets.randbelow(10)) for _ in range(6))


      return otp

  def verify_otp(self, email: str, otp:str) -> bool:

      print("=" * 60)
      print("VERIFY OTP")
      print(f"Email : {email}")
      print(f"OTP : {otp}")
      print("=" * 60)


      return True





otp_service = OTPService()



