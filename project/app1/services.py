import asyncio
from fastmcp import Client
from .mcp_tools import mcp
from .mcp_context import current_user_var

#to call the async block inside sync code usign asyncio
def run_tool_call_sync(user,tool_name:str,args):
    return asyncio.run(run_tool_call(user,tool_name,args))


async def run_tool_call(user,tool:str, args)->dict:
    token = current_user_var.set(user)     # stash real user for this call only
    try:
        async with Client(mcp) as client:  # <-- Client(mcp): in-memory connection
            result = await client.call_tool(tool, args)
            if result.is_error:
                raise RuntimeError(str(result.content))
            return result.data
    finally:
        current_user_var.reset(token)