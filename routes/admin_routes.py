from flask import Blueprint, render_template, session, redirect, url_for, request, flash, current_app
from database import get_connection
import os
from werkzeug.utils import secure_filename
from services.job_service import fetch_jobs
from services.email_service import send_job_alert

admin = Blueprint("admin", __name__)

def get_grouped_companies():
    conn = get_connection()
    # Fetch all job roles and group them by company
    rows = conn.execute("SELECT * FROM company").fetchall()
    conn.close()

    companies_dict = {}
    for row in rows:
        name = row["company_name"]
        if name not in companies_dict:
            companies_dict[name] = {
                "company_name": name,
                "official_page_link": row["official_page_link"],
                "image_filename": row["image_filename"],
                "jobs": []
            }
        
        # Only add job info if job_role is present
        if row["job_role"]:
            companies_dict[name]["jobs"].append({
                "id": row["id"],
                "job_role": row["job_role"],
                "start_date": row["start_date"],
                "end_date": row["end_date"],
                "location": row["location"]
            })
    
    return list(companies_dict.values())

@admin.route("/admin")
def dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("auth.login"))

    conn = get_connection()
    users = conn.execute("SELECT * FROM user WHERE role = 'user'").fetchall()
    conn.close()

    companies = get_grouped_companies()

    return render_template("admin/dashboard.html", 
                           username=session.get("username"),
                           users=users, 
                           companies=companies)

@admin.route("/add-company", methods=["POST"])
def add_company():
    if session.get("role") != "admin":
        return redirect(url_for("auth.login"))

    company_name = request.form.get("company_name")
    official_page_link = request.form.get("official_page_link")
    
    if not company_name or not official_page_link:
        flash("Company name and official link are required", "error")
        return redirect(url_for("admin.dashboard"))

    # Fetch jobs from API automatically
    try:
        jobs = fetch_jobs(company_name)
    except Exception as e:
        print(f"Error fetching jobs: {e}")
        jobs = []

    conn = get_connection()
    
    if jobs:
        new_jobs_count = 0
        for job in jobs:
            # Check if job already exists to avoid duplicates
            existing = conn.execute(
                "SELECT id FROM company WHERE company_name = ? AND job_role = ?",
                (company_name, job["role"])
            ).fetchone()
            
            if not existing:
                conn.execute(
                    "INSERT INTO company (company_name, official_page_link, job_role, start_date, end_date, location) VALUES (?, ?, ?, ?, ?, ?)",
                    (company_name, official_page_link, job["role"], "Active", "TBD", job.get("location", "Remote"))
                )
                new_jobs_count += 1
        
        if new_jobs_count > 0:
            flash(f"Company added and {new_jobs_count} job roles synced!", "success")
        else:
            flash("Company added (no new job roles found)", "info")
    else:
        # If no jobs found, at least create a company entry if it doesn't exist
        existing_comp = conn.execute("SELECT id FROM company WHERE company_name = ?", (company_name,)).fetchone()
        if not existing_comp:
            conn.execute(
                "INSERT INTO company (company_name, official_page_link) VALUES (?, ?)",
                (company_name, official_page_link)
            )
            flash("Company added but no jobs found on API", "warning")
        else:
            flash("Company already exists and no new jobs found", "info")
        
    conn.commit()
    conn.close()
    
    return redirect(url_for("admin.dashboard"))

@admin.route("/delete-user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    if session.get("role") != "admin":
        return redirect(url_for("auth.login"))
        
    conn = get_connection()
    conn.execute("DELETE FROM user WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash("User deleted successfully!", "success")
    return redirect(url_for("admin.dashboard"))

@admin.route("/delete-company/<int:company_id>", methods=["POST"])
def delete_company(company_id):
    if session.get("role") != "admin":
        return redirect(url_for("auth.login"))
        
    conn = get_connection()
    conn.execute("DELETE FROM company WHERE id = ?", (company_id,))
    conn.commit()
    conn.close()
    flash("Job role deleted successfully!", "success")
    return redirect(url_for("admin.dashboard"))

@admin.route("/sync-all-jobs", methods=["POST"])
def sync_all_jobs():
    if session.get("role") != "admin":
        return redirect(url_for("auth.login"))
        
    conn = get_connection()
    # Fetch data and close connection immediately to avoid locking during network calls
    companies = conn.execute("SELECT DISTINCT company_name, official_page_link, image_filename FROM company").fetchall()
    conn.close()
    
    sync_count = 0
    for comp in companies:
        try:
            # Perform slow network request WITHOUT an open DB connection
            jobs = fetch_jobs(comp["company_name"])
            
            # Open a new connection for the updates
            conn = get_connection()
            for job in jobs:
                # Check if job already exists
                existing = conn.execute(
                    "SELECT id FROM company WHERE company_name = ? AND job_role = ?",
                    (comp["company_name"], job["role"])
                ).fetchone()
                
                if not existing:
                    conn.execute(
                        "INSERT INTO company (company_name, official_page_link, image_filename, job_role, start_date, end_date, location) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (comp["company_name"], comp["official_page_link"] or job.get("link", ""), comp["image_filename"], job["role"], "Active", "TBD", job.get("location", "Remote"))
                    )
                    sync_count += 1
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error syncing {comp['company_name']}: {e}")
            continue

    flash(f"Synced {sync_count} new job roles!", "success")
    return redirect(url_for("admin.dashboard"))

    
    conn.commit()
    conn.close()
    flash(f"Synced {sync_count} new job roles!", "success")
    return redirect(url_for("admin.dashboard"))

@admin.route("/notify-users", methods=["POST"])
def notify_users():
    if session.get("role") != "admin":
        return redirect(url_for("auth.login"))
        
    conn = get_connection()
    users = conn.execute("SELECT * FROM user WHERE role = 'user'").fetchall()
    companies = conn.execute("SELECT * FROM company WHERE job_role IS NOT NULL").fetchall()
    
    notified_count = 0
    for user in users:
        if not user["email"] or not user["applied_job"]:
            continue
            
        interested_job = user["applied_job"].lower()
        for comp in companies:
            if interested_job in comp["job_role"].lower():
                # Send email
                if send_job_alert(user["email"], user["username"], comp["company_name"], comp["job_role"], comp["official_page_link"]):
                    notified_count += 1
                    break # Only notify once for one match for now
                    
    conn.close()
    flash(f"Sent notifications to {notified_count} users!", "success")
    return redirect(url_for("admin.dashboard"))
