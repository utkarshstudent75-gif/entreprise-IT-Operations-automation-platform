import os

from pydantic import BaseModel, EmailStr, Field

EXAMPLE_EMAIL = "user@example.com"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(
        ...,
        description=(
            "The email address associated with the account to reset the password."
        ),
        examples=[EXAMPLE_EMAIL],
    )

    model_config = {"json_schema_extra": {"example": {"email": EXAMPLE_EMAIL}}}


class VerifyOtpRequest(BaseModel):
    email: EmailStr = Field(
        ...,
        description="The email address associated with the account.",
        examples=[EXAMPLE_EMAIL],
    )
    otp: str = Field(
        ...,
        description="The one-time password (OTP) code received by the user.",
        examples=["123456"],
    )

    model_config = {
        "json_schema_extra": {"example": {"email": EXAMPLE_EMAIL, "otp": "123456"}}
    }


class ResetPasswordRequest(BaseModel):
    email: EmailStr = Field(
        ...,
        description="The email address associated with the account.",
        examples=[EXAMPLE_EMAIL],
    )
    otp: str = Field(
        ...,
        description="The verified one-time password (OTP) code.",
        examples=["123456"],
    )
    new_password: str = Field(
        ...,
        description="The new secure password to set for the account.",
        examples=["NewSecurePassword123!"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": EXAMPLE_EMAIL,
                "otp": "123456",
                "new_password": os.getenv("NEW_P", "NewSecurePassword123!"),  # nosec B105
            }
        }
    }


class PasswordResponse(BaseModel):
    message: str = Field(
        ...,
        description=(
            "A user-friendly status message describing the result of the operation."
        ),
        examples=["OTP verified successfully."],
    )

    model_config = {
        "json_schema_extra": {"example": {"message": "OTP verified successfully."}}
    }
