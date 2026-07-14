import random


    class PasswordService:

        def request_password_reset(self, email: str):

            otp = otp_service.generate_otp()

            print("=" *50)
            print(f"Generated OTP for {email}:{otp}")
            print("=" *50)


            return True


password_service = PasswordService()        
