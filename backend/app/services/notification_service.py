from app.core.logging_config import logger
from app.core.config import settings

class NotificationService:
    """
    Responsible for sending notifications to users.
    

    Today: 
    - Prints OTP to the console for demonstration purposes.

    Future:
        - SMS node
        - Azure Communication Services
        - Email

    """ 

    def send_otp(self, email: str, otp: str) -> None:
       
        
        if settings.DEBUG:
            logger.info("OTP for %s: %s", email, otp)
        else:
            logger.info("OTP generated for %s", email)

notification_service = NotificationService()