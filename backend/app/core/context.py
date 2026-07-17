import contextvars

# Context variables to hold request-scoped metadata
request_ip: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_ip", default=None)
request_user_agent: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_user_agent", default=None)
request_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)
