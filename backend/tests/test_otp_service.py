from app.services.otp_service import otp_service


def test_generate_otp():

    otp = otp_service.generate_otp("test@example.com")

    assert len(otp) == 6
