
from fastmcp import FastMCP
from .models import Resume
from .mcp_context import current_user_var


mcp = FastMCP("JobSeeker Tools")   # <-- FastMCP server instance

@mcp.tool
def get_last_two_resumes() -> list[dict]:
    """Get the current user's two most recently uploaded resumes."""
    user = current_user_var.get()          # injected by YOUR code, not the LLM
    resumes = Resume.objects.filter(
        user__user=user
    ).order_by("-uploaded_time")[:2]
    return [{"id": r.id, "uploaded_time": str(r.uploaded_time)} for r in resumes]

