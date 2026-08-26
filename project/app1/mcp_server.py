from fastmcp import FastMCP
from .models import *

mcp=FastMCP("JobSeeker Tools")

@mcp.tool
def get_last_two_resume()->dict:
    Resume.objects.filter(user__user=request.user).order_by("-uploaded_time")[:1] #problem here
    