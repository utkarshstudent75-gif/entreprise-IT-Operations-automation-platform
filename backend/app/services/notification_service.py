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
       
        print("=" * 60)
        print("OTP Notification")
        print(f"Recipient: {email}")
        print(f"OTP : {otp}")
        print("=" * 60)

notification_service = NotificationService()