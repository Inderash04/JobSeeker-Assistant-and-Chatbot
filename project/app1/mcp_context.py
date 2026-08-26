from contextvars import ContextVar

current_user_var: ContextVar = ContextVar("current_user")