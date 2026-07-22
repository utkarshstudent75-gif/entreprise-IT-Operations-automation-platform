from pydantic import BaseModel, Field


class SmsRequest(BaseModel):
    """
    Data Transfer Object (DTO) for sending SMS notifications.

    STRICT PRIVACY REQUIREMENT:
    This object carries ONLY the minimum essential data required for SMS delivery
    (destination phone number and message body). Domain models (User, Ticket, AuditLog),
    credentials, session info, or enterprise identity attributes must NEVER be attached.
    """

    phone_number: str = Field(..., description="Destination phone number")
    message: str = Field(..., description="SMS message text")
