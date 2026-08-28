
from fastmcp import FastMCP
from .models import Resume
from .mcp_context import current_user_var
import os
import requests
from dotenv import load_dotenv
load_dotenv()

mcp = FastMCP("JobSeeker Tools")   # <-- FastMCP server instance

@mcp.tool
def get_last_two_resumes() -> list[dict]:
    """Get the current user's two most recently uploaded resumes."""
    user = current_user_var.get()          # injected by YOUR code, not the LLM
    resumes = Resume.objects.filter(user__user=user).order_by("-uploaded_time")[:2]
    return [{"resume_summary":r.resume_summary, "uploaded_time": str(r.uploaded_time)} for r in resumes]

@mcp.tool
def get_github_summary()->list[dict]:
    user=current_user_var.get()
    github_summary=Resume.objects.filter(user__user=user).order_by("-uploaded_time").first()
    return [{"github_summary":r.github_summary,"uploaded_time":r.uploaded_time} for r in github_summary]

@mcp.tool
def find_job_listings(location:str,job_title : str="", max_results : int=10) -> list[dict]:
    ADZUNA_APP_ID=os.environ.get("Application_ID")
    ADZUNA_APP_KEY=os.environ.get("Application_Keys")
    url="https://api.adzuna.com/v1/api/jobs/in/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": max_results,
        "what": job_title,
        "content-type": "application/json",
    }
    if location:
        params["where"]=location
    try:
        resp=requests.get(url=url,params=params,timeout=10)
        resp.raise_for_status()
        data=resp.json()
    except requests.exceptions.RequestException as e:
        print(f"error occurred in calling Adzuna jobs api: {str(e)}")
        raise RuntimeError(f"Adzuna request failed: {e}")
    except Exception as e:
        print(f"error occurredin job listing script: {str(e)}")
        return [{"error":str(e)}]

    jobs = []
    for r in data.get("results", []):
        jobs.append({
            "title": r.get("title"),
            "company": r.get("company", {}).get("display_name"),
            "location": r.get("location", {}).get("display_name"),
            "salary_min": r.get("salary_min"),
            "salary_max": r.get("salary_max"),
            "salary_is_predicted": r.get("salary_is_predicted"),
            "posted": r.get("created"),
            "description_snippet": (r.get("description") or "")[:200],
            "url": r.get("redirect_url"),
        })
    return jobs
