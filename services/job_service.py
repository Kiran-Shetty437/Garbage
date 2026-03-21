import requests
import re
from datetime import datetime, timezone
from config import ADZUNA_APP_ID, ADZUNA_APP_KEY


BASE_URL = "https://api.adzuna.com/v1/api/jobs/in/search/"


def clean_html(text):
    """Remove HTML tags from Adzuna text fields."""
    if not text: return ""
    return re.sub(r'<[^>]*>', '', text)


def role_match(job_title, role_keywords):
    job_title = clean_html(job_title).lower()
    words = role_keywords.lower().split()
    return all(word in job_title for word in words)


# ✅ NEW: check if job link active
def is_job_active(link):
    try:
        r = requests.head(link, allow_redirects=True, timeout=5)
        return r.status_code == 200
    except:
        return False


# ✅ NEW: extract experience level
def extract_experience(title, description):
    title_clean = clean_html(title).lower()
    desc_clean = clean_html(description).lower()
    full_text = f"{title_clean} {desc_clean}"

    fresher_keywords = [
        "fresher", "freshers", "entry level",
        "graduate", "0 years", "0-1 years", "no experience", "intern", "trainee", "entry-level"
    ]

    senior_keywords = [
        "senior", "sr.", "sr ", "lead", "architect", "manager", "staff", 
        "principal", "avp", "vp", "director", "head", "specialist", "expert"
    ]

    # 1. Check for explicit year patterns in description or title (most accurate)
    # Matches: 5 years, 3-5 yrs, 2+ yr, 4 to 6 years
    match = re.search(r'(\d+)\s*(?:\+?)\s*(?:-|to)?\s*(\d+)?\s*(?:years|yrs|year|yr)', full_text)
    if match:
        start = match.group(1)
        end = match.group(2)
        if end:
            return "Experienced", f"{start}-{end} years"
        else:
            return "Experienced", f"{start}+ years"

    # 2. Check for Fresher keywords (whole word)
    for word in fresher_keywords:
        if re.search(rf"\b{re.escape(word)}\b", full_text):
            return "Fresher", "0-1 years"

    # 3. Check for Seniority keywords in title (internal match is fine for titles)
    for word in senior_keywords:
        if word in title_clean:
            return "Experienced", "Senior Level"

    # 4. Junior check
    if any(word in title_clean for word in ["jr.", "jr ", "junior"]):
        return "Junior", "0-2 years"

    return "Not specified", "Not specified"


import concurrent.futures

def fetch_filtered_jobs(companies, roles, days_limit=30, fetch_all=False):
    """Fetch jobs from Adzuna API with high concurrency for link checking."""
    collected_jobs = []
    seen_links = set()
    today = datetime.now(timezone.utc)

    # Use a thread pool to check link status in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as check_executor:
        
        for company in companies:
            # Reduced page limit from 10 to 5 for speed (~250 possible jobs per organization)
            for page in range(1, 6):
                params = {
                    "app_id": ADZUNA_APP_ID,
                    "app_key": ADZUNA_APP_KEY,
                    "results_per_page": 50,
                    "what": company
                }

                try:
                    response = requests.get(BASE_URL + str(page), params=params, timeout=10)
                    if response.status_code != 200: break
                    
                    data = response.json()
                    jobs = data.get("results", [])
                    if not jobs: break

                    # Preparatory list for concurrent checking
                    possible_jobs = []

                    for job in jobs:
                        company_name = clean_html(job.get("company", {}).get("display_name") or "Not specified")
                        title = clean_html(job.get("title") or "Not specified")
                        location = clean_html(job.get("location", {}).get("display_name") or "Not specified")
                        date_str = job.get("created", "")
                        link = job.get("redirect_url") or ""
                        description = job.get("description") or ""

                        if not link or link in seen_links: continue
                        seen_links.add(link)

                        # Filtering logic
                        if company.lower() not in company_name.lower(): continue
                        
                        if not fetch_all and roles:
                            if not any(role_match(title, role) for role in roles): continue

                        try:
                            job_date = datetime.strptime(date_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                        except: continue

                        if (today - job_date).days > days_limit: continue
                        
                        # Add to queue for link checking
                        possible_jobs.append({
                            "company": company_name,
                            "role": title,
                            "location": location,
                            "date": job_date.strftime("%Y-%m-%d"),
                            "level": "Scanning...",
                            "experience": "Scanning...",
                            "description": description,
                            "link": link
                        })

                    # Perform parallel link checking and experience extraction
                    def process_job_full(pj):
                        pj["active"] = is_job_active(pj["link"])
                        lvl, exp = extract_experience(pj["role"], pj["description"])
                        pj["level"] = lvl
                        pj["experience"] = exp
                        # Remove description to save memory/DB space
                        del pj["description"]
                        return pj

                    futures = {check_executor.submit(process_job_full, p): p for p in possible_jobs}
                    for future in concurrent.futures.as_completed(futures):
                        collected_jobs.append(future.result())

                except Exception as e:
                    print(f"Error fetching page {page} for {company}: {e}")
                    break

    return collected_jobs


def fetch_jobs(company_name, roles=None, fetch_all=False):
    if fetch_all:
        return fetch_filtered_jobs([company_name], roles=[], fetch_all=True)

    if not roles:
        from database import get_connection
        try:
            conn = get_connection()
            users = conn.execute("SELECT applied_job FROM user WHERE applied_job IS NOT NULL AND applied_job != ''").fetchall()
            conn.close()
            
            dynamic_roles = {"software engineer", "software developer", "python developer"}
            for user in users:
                parts = [p.strip().lower() for p in user["applied_job"].split(',')]
                for p in parts:
                    if p: dynamic_roles.add(p)
            roles = list(dynamic_roles)
        except Exception as e:
            print(f"Warning: Database error in job_service fetching roles: {e}")
            roles = ["software engineer", "software developer", "python developer"]

    return fetch_filtered_jobs([company_name], roles, fetch_all=fetch_all)


def check_and_notify_user(user_id, conn=None):
    from database import get_connection
    from services.email_service import send_job_alert
    
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True
        
    user = conn.execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
    if not user or not user["email"] or not user["applied_job"]:
        if should_close: conn.close()
        return
        
    interested_roles = [role.strip().lower() for role in user["applied_job"].split(',')]
    companies = conn.execute("SELECT * FROM company WHERE job_role IS NOT NULL").fetchall()
    
    for comp in companies:
        job_role_lower = comp["job_role"].lower()
        match_found = False
        for role in interested_roles:
            if role in job_role_lower or job_role_lower in role:
                match_found = True
                break
                
        if match_found:
            check = conn.execute("SELECT id FROM notifications WHERE user_id = ? AND company_id = ?", (user["id"], comp["id"])).fetchone()
            if not check:
                if send_job_alert(user["email"], user["username"], comp["company_name"], comp["job_role"], comp["official_page_link"]):
                    conn.execute("INSERT INTO notifications (user_id, company_id) VALUES (?, ?)", (user["id"], comp["id"]))
                    conn.commit()
                    
    if should_close: conn.close()


def sync_company_jobs(company_name, official_page_link, image_filename=None, conn=None):
    from database import get_connection
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True
        
    sync_count = 0
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        jobs = fetch_jobs(company_name, fetch_all=True)
        api_job_roles = {job["role"] for job in jobs}
        
        db_jobs = conn.execute("SELECT id, job_role FROM company WHERE company_name = ? AND job_role IS NOT NULL", (company_name,)).fetchall()
        
        for db_job in db_jobs:
            if db_job["job_role"] not in api_job_roles:
                conn.execute("DELETE FROM notifications WHERE company_id = ?", (db_job["id"],))
                conn.execute("DELETE FROM company WHERE id = ?", (db_job["id"],))
        
        for job in jobs:
            existing = conn.execute("SELECT id FROM company WHERE company_name = ? AND job_role = ?", (company_name, job["role"])).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO company (company_name, official_page_link, image_filename, job_role, start_date, end_date, location, job_level, experience_required, apply_link, is_active, last_sync) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (company_name, official_page_link, image_filename, job["role"], "Active", "TBD", job.get("location", "Remote"), job.get("level"), job.get("experience"), job.get("link"), 1 if job.get("active") else 0, now_str)
                )
                sync_count += 1
            else:
                conn.execute(
                    "UPDATE company SET job_level = ?, experience_required = ?, is_active = ?, location = ?, apply_link = ?, last_sync = ? WHERE id = ?",
                    (job.get("level"), job.get("experience"), 1 if job.get("active") else 0, job.get("location"), job.get("link"), now_str, existing["id"])
                )
        
        conn.execute("UPDATE company SET last_sync = ? WHERE company_name = ?", (now_str, company_name))
        conn.commit()
    except Exception as e:
        print(f"Error syncing {company_name}: {e}")
    finally:
        if should_close: conn.close()
    return sync_count


def sync_all_companies():
    """Sync all followed companies and notify users in parallel."""
    from database import get_connection
    conn = get_connection()
    companies = conn.execute("SELECT DISTINCT company_name, official_page_link, image_filename FROM company").fetchall()
    conn.close()
    
    total_sync = 0
    # Process multiple companies concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as company_executor:
        futures = [company_executor.submit(sync_company_jobs, comp["company_name"], comp["official_page_link"], comp["image_filename"]) for comp in companies]
        for future in concurrent.futures.as_completed(futures):
            total_sync += future.result()
    
    # Notifications section (can remain sequential or also be parallelized if mailing is the bottleneck)
    conn = get_connection()
    users = conn.execute("SELECT id FROM user WHERE role = 'user' AND email IS NOT NULL AND applied_job IS NOT NULL").fetchall()
    for u in users:
        check_and_notify_user(u["id"], conn)
    conn.close()
    
    return total_sync
