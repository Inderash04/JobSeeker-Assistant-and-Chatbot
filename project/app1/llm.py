
import os
from openai import OpenAI
from dotenv import load_dotenv #Steps---->  from dotenv import load_dotenv ----->
#   --->done using load_dotenv() to make the .env visible to os---> 
# ---->then use os.environ.get("GROQ_API_KEY")

import time

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

def LLM_bot(messages):
    ret_d={}
    start=time.time()
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages
    )
    elapsed_time=time.time()-start
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
    
    return ret_d

#-------------------------------------------------
#Connecting mcp and chat step 2 - 1.in views.py
#-------------------------------------------------
def chat_with_tools(user_message,request):
    