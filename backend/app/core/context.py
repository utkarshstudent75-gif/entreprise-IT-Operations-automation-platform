import contextvars
from contextlib import contextmanager

# Context variables to hold request-scoped metadata
request_ip: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_ip", default=None)
request_user_agent: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_user_agent", default=None)
request_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)
user_id: contextvars.ContextVar[str | int | None] = contextvars.ContextVar("user_id", default=None)
action: contextvars.ContextVar[str | None] = contextvars.ContextVar("action", default=None)


@contextmanager
def logging_context(act: str | None = None, u_id: str | int | None = None):
    """
    Context manager to set logging context variables and safely restore them.
    """
    old_act = action.get()
    old_uid = user_id.get()
    if act is not None:
        action.set(act)
    if u_id is not None:
        user_id.set(u_id)
    try:
        yield
    finally:
        action.set(old_act)
        user_id.set(old_uid)

