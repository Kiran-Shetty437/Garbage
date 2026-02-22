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
    official_link = request.form.get("official_link")
    manual_role = request.form.get("manual_role")
    manual_start = request.form.get("manual_start")
    manual_end = request.form.get("manual_end")
    
    image_filename = None
    if "company_image" in request.files:
        file = request.files["company_image"]
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
            image_filename = filename

    conn = get_connection()
    
    # If manual role is provided, add it directly
    if manual_role:
        manual_location = request.form.get("manual_location", "Remote")
        conn.execute(
            "INSERT INTO company (company_name, official_page_link, image_filename, job_role, start_date, end_date, location) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (company_name, official_link, image_filename, manual_role, manual_start, manual_end, manual_location)
        )
    else:
        # Just add the company entry without a job role if no manual role
        conn.execute(
            "INSERT INTO company (company_name, official_page_link, image_filename) VALUES (?, ?, ?)",
            (company_name, official_link, image_filename)
        )
        
    conn.commit()
    conn.close()
    
    flash("Company added successfully!", "success")
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
    companies = conn.execute("SELECT DISTINCT company_name, official_page_link, image_filename FROM company").fetchall()
    
    sync_count = 0
    for comp in companies:
        jobs = fetch_jobs(comp["company_name"])
        for job in jobs:
            # Check if job already exists to avoid duplicates
            existing = conn.execute(
                "SELECT id FROM company WHERE company_name = ? AND job_role = ?",
                (comp["company_name"], job["role"])
            ).fetchone()
            
            if not existing:
                conn.execute(
                    "INSERT INTO company (company_name, official_page_link, image_filename, job_role, start_date, end_date, location) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (comp["company_name"], comp["official_page_link"], comp["image_filename"], job["role"], "Active", "TBD", job.get("location", "Remote"))
                )
                sync_count += 1

    
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
