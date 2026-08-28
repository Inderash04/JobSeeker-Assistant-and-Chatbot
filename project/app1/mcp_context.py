from contextvars import ContextVar

current_user_var: ContextVar = ContextVar("current_user")

#current_user_var is used here because  .....

#We are passing `request.user` into a function call that happens milliseconds later in the same process)

#`contextvars` exists to pass data **within a single execution flow, in-memory, in the same process, for the lifetime of one call**. It's essentially free — no serialization, no network hop, no external service. It disappears the instant `run_tool_call` finishes (that's what `.reset(token)` does). There's nothing to clean up, nothing to expire, nothing that can go stale.

