import requests
import datetime
from config import ADZUNA_APP_ID, ADZUNA_APP_KEY


def fetch_jobs(company):

    jobs = []

    for page in range(1, 3):

        url = f"https://api.adzuna.com/v1/api/jobs/in/search/{page}"

        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "what": company
        }

        r = requests.get(url, params=params)

        if r.status_code != 200:
            break

        data = r.json()

        for job in data["results"]:
            jobs.append({
                "role": job["title"],
                "company": job["company"]["display_name"],
                "link": job["redirect_url"],
                "location": job.get("location", {}).get("display_name", "Remote")
            })


    return jobs