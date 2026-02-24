import requests
from datetime import datetime, timezone
from config import ADZUNA_APP_ID, ADZUNA_APP_KEY


BASE_URL = "https://api.adzuna.com/v1/api/jobs/in/search/"


def role_match(job_title, role_keywords):
    job_title = job_title.lower()
    words = role_keywords.lower().split()
    return all(word in job_title for word in words)


def fetch_filtered_jobs(companies, roles, days_limit=30):

    collected_jobs = []
    seen_links = set()
    today = datetime.now(timezone.utc)

    for company in companies:

        for page in range(1, 10):

            params = {
                "app_id": ADZUNA_APP_ID,
                "app_key": ADZUNA_APP_KEY,
                "results_per_page": 50,
                "what": company
            }

            response = requests.get(BASE_URL + str(page), params=params)

            if response.status_code != 200:
                break

            data = response.json()
            jobs = data.get("results", [])

            if not jobs:
                break

            for job in jobs:

                company_name = job.get("company", {}).get("display_name", "")
                title = job.get("title", "")
                location = job.get("location", {}).get("display_name", "Remote")
                date_str = job.get("created", "")
                link = job.get("redirect_url", "")

                # Skip duplicate
                if not link or link in seen_links:
                    continue

                seen_links.add(link)

                # Company filter
                if company.lower() not in company_name.lower():
                    continue

                # Role filter
                if not any(role_match(title, role) for role in roles):
                    continue

                # Date filter
                try:
                    job_date = datetime.strptime(date_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                except:
                    continue

                if (today - job_date).days > days_limit:
                    continue

                # Save valid job
                collected_jobs.append({
                    "company": company_name,
                    "role": title,
                    "location": location,
                    "date": job_date.strftime("%Y-%m-%d"),
                    "link": link
                })

    return collected_jobs


def fetch_jobs(company_name):
    """
    Wrapper for fetch_filtered_jobs to match the expected signature in admin_routes.py.
    """
    default_roles = ["software engineer", "software developer", "python developer"]
    return fetch_filtered_jobs([company_name], default_roles)
