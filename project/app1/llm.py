
import os
from openai import OpenAI
from dotenv import load_dotenv #Steps---->  from dotenv import load_dotenv ----->
#   --->done using load_dotenv() to make the .env visible to os---> 
# ---->then use os.environ.get("GROQ_API_KEY")

import time
import logging
logger=logging.getLogger(__name__)

load_dotenv()
key=os.environ.get("GROQ_API_KEY")
print("KEY EXISTS:", key is not None)
print("KEY LENGTH:", len(key) if key else 0)
print("KEY PREFIX:", key[:10] if key else None)

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

def LLM_bot(messages):
    logger.info("message sent to LLM_bot func")
    ret_d={}
    start=time.time()
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages              
        )
        elapsed_time=time.time()-start

    except Exception as e:
        logger.exception("Received some error from LLM")
        
    try:
        usage = response.usage
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens
        total_tokens = usage.total_tokens
        
        ret_d["bot_message"]=response.choices[0].message.content
        ret_d["usage"]=usage
        ret_d["prompt_tokens"]=prompt_tokens
        ret_d["completion_tokens"]=completion_tokens
        ret_d["total_tokens"]=total_tokens
        ret_d["elapsed_time"]=elapsed_time
    except Exception as e:
        logger.exception("Error in updating model")

    logger.info("exiting LLM_bot func")
    return ret_d


def LLM_to_MCP(messages, tools=None):
    ret_d = {}
    logger.info("JobSeeker request sent to LLM_to_MCP")
    try:
        response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages,
        tools=tools,          # <-- pass tool definitions
        tool_choice="auto" if tools else None,
        )
        logger.info("JobSeeker LLM 200 OK")

    except Exception as e:
        logger.exception("LLM_to_MCP failed")

    try:
        usage = response.usage
        message = response.choices[0].message
        ret_d["bot_message"] = message.content
        ret_d["tool_calls"] = message.tool_calls   # <-- None, or a list of calls the model wants to make
        ret_d["raw_message"] = message              # keep the full message object — you'll need to append it back
    except Exception as e:
        logger.exception("Error in fetching details from response of function LLM_to_MCP")
    return ret_d

#-------------------------------------------------
#Connecting mcp and chat step 2 - 1.in views.py
#-------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_last_two_resumes",
            "description": "Get the current user's two most recently uploaded resumes.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_github_summary",
            "description": "Get the GitHub summary from the current user's most recently uploaded resume.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_job_listings",
            "description": "Find job listings based on location and an optional job title.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The location where the jobs should be searched."
                    },
                    "job_title": {
                        "type": "string",
                        "description": "The job title or keywords to search for.",
                        "default": ""
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of job listings to return.",
                        "default": 10
                    }
                },
                "required": ["location"]
            }
        }
    }
]
import json
from .services import run_tool_call_sync  # from earlier in our conversation

def chat_with_tools(request, user_message: str) -> str:
    messages = [{"role": "user", "content": user_message}]

    result = LLM_to_MCP(messages, tools=TOOLS)
    logger.info("chat_with_tools function called")
    
    if result["tool_calls"]:
        # Append the assistant's tool-call message back into history — required by the API
        messages.append(result["raw_message"])

        for tool_call in result["tool_calls"]:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)  # string -> dict

            # === SECURITY BOUNDARY, same as before ===
            # tool_args comes from the model — never trust it for identity.
            # request.user is injected by YOUR code, not the model.
            tool_result = run_tool_call_sync(request.user, tool_name, tool_args)

            # Feed the result back as a "tool" role message
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result),
            })

        # Second call: let the model use the tool result to write a final answer
        final = LLM_to_MCP(messages, tools=TOOLS)
        return final["bot_message"]

    return result["bot_message"]