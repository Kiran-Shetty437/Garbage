import requests
from datetime import datetime, timedelta, timezone

# ==============================
# ENTER YOUR ADZUNA API DETAILS
# ==============================

APP_ID = "0e1073f3"
APP_KEY = "808b2c50d0ec371860f1be44c2de724d"

# ==============================
# ADMIN INPUT
# ==============================

COMPANIES = [
    "Google",
    "Amazon",
    "Microsoft",
    "IBM",
    "Infosys",
    "TCS",
    "Wipro"
]

ROLES = [
    "software engineer",
    "software developer",
    "python developer"
]

# collect only last X days jobs
DAYS_LIMIT = 30


# ==============================
# FUNCTION: FLEXIBLE ROLE MATCH
# ==============================

def role_match(job_title, role_keywords):

    job_title = job_title.lower()
    words = role_keywords.lower().split()

    return all(word in job_title for word in words)


# ==============================
# MAIN CODE
# ==============================

base_url = "https://api.adzuna.com/v1/api/jobs/in/search/"

collected_jobs = []
seen_links = set()

today = datetime.now(timezone.utc)

for company in COMPANIES:

    print(f"\nChecking company: {company}")

    for page in range(1, 10):

        params = {
            "app_id": APP_ID,
            "app_key": APP_KEY,
            "results_per_page": 50,
            "what": company
        }

        response = requests.get(base_url + str(page), params=params)

        if response.status_code != 200:
            print("API Error:", response.status_code)
            break

        data = response.json()
        jobs = data.get("results", [])

        if not jobs:
            break

        for job in jobs:

            company_name = job.get("company", {}).get("display_name", "")
            title = job.get("title", "")
            location = job.get("location", {}).get("display_name", "")
            date_str = job.get("created", "")
            link = job.get("redirect_url", "")

            # skip if no link or duplicate
            if not link or link in seen_links:
                continue

            seen_links.add(link)

            # check company match
            if company.lower() not in company_name.lower():
                continue

            # check role match
            matched = False

            for role in ROLES:

                if role_match(title, role):
                    matched = True
                    break

            if not matched:
                continue

            # check date
            try:
                job_date = datetime.strptime(date_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except:
                continue

            if (today - job_date).days > DAYS_LIMIT:
                continue

            # save job
            collected_jobs.append({
                "company": company_name,
                "role": title,
                "location": location,
                "date": job_date.strftime("%Y-%m-%d"),
                "link": link
            })


# ==============================
# PRINT RESULTS
# ==============================

print("\n\nFINAL FILTERED JOBS")
print("="*60)

for job in collected_jobs:

    print("Company:", job["company"])
    print("Role:", job["role"])
    print("Location:", job["location"])
    print("Posted Date:", job["date"])
    print("Apply Link:", job["link"])
    print("-"*60)

print("Total jobs found:", len(collected_jobs))