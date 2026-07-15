from app.services.otp_service import otp_service
from app.services.notification_service import notification_service


class PasswordService:

        def request_password_reset(self, email: str):

            otp = otp_service.generate_otp(email)

            notification_service.send_otp(email, otp)

            return True


password_service = PasswordService()        
