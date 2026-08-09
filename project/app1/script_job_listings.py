from dotenv import load_dotenv
import requests
import sys
import json
import os
load_dotenv()


ADZUNA_APP_ID=os.environ.get("Application_ID")
ADZUNA_APP_KEY=os.environ.get("Application_Keys")


url="https://api.adzuna.com/v1/api/jobs/in/search/1"

def find_job_listings(location:str,job_title : str=" ", max_results : int=10) -> list[dict]:
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
        return [{"error":str(e)}]
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


if __name__== "__main__":
    location=sys.argv[1]
    job=[]
    for i in sys.argv[2:]:
        job.append(i)
    job_title=" ".join(job)
    print(json.dumps(find_job_listings(location,job_title),indent=2))
