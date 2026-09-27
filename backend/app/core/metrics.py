from fastapi import FastAPI, Request
from prometheus_client import Counter
from prometheus_fastapi_instrumentator import Instrumentator

password_reset_events = Counter(
    "eitoap_password_reset_events_total",
    "Password reset requests and completions by stage and outcome.",
    ("stage", "outcome"),
)
otp_verifications = Counter(
    "eitoap_otp_verifications_total",
    "Password reset OTP verification attempts by outcome.",
    ("outcome",),
)
authentication_failures = Counter(
    "eitoap_authentication_failures_total",
    "HTTP authentication and authorization failures.",
    ("status_code",),
)


def instrument_app(app: FastAPI) -> None:
    @app.middleware("http")
    async def count_authentication_failures(request: Request, call_next):
        response = await call_next(request)
        if response.status_code in (401, 403):
            authentication_failures.labels(status_code=str(response.status_code)).inc()
        return response

    Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        excluded_handlers=["/metrics", "/api/v1/metrics"],
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
