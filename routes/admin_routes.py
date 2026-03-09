from flask import Blueprint, render_template, session, redirect, url_for, request, flash, current_app, jsonify
from services.resume_service import analyze_resume_image
from database import get_connection
import os
from werkzeug.utils import secure_filename
from services.job_service import fetch_jobs
from services.email_service import send_job_alert

admin = Blueprint("admin", __name__)

def check_and_notify_user(user_id, conn=None):
    """
    Automatically check if a user matches any existing company jobs
    and send an email if a match is found.
    """
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
            # Check if already notified
            check = conn.execute(
                "SELECT id FROM notifications WHERE user_id = ? AND company_id = ?",
                (user["id"], comp["id"])
            ).fetchone()
            
            if not check:
                if send_job_alert(user["email"], user["username"], comp["company_name"], comp["job_role"], comp["official_page_link"]):
                    conn.execute(
                        "INSERT INTO notifications (user_id, company_id) VALUES (?, ?)",
                        (user["id"], comp["id"])
                    )
                    conn.commit()
                    
    if should_close:
        conn.close()

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
                "location": row["location"],
                "job_level": row["job_level"],
                "experience_required": row["experience_required"],
                "is_active": row["is_active"]
            })
    
    return list(companies_dict.values())

@admin.route("/admin")
@admin.route("/admin/dashboard")
def dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("auth.login"))

    conn = get_connection()
    users = conn.execute("SELECT * FROM user WHERE role = 'user' ORDER BY created_at DESC").fetchall()
    
    # Fetch global settings
    ratio_row = conn.execute("SELECT value FROM global_settings WHERE key = 'commission_ratio'").fetchone()
    commission_ratio = ratio_row["value"] if ratio_row else "10.0"
    
    # Calculate some stats for the dashboard
    total_users = len(users)
    active_today = conn.execute("SELECT COUNT(*) as count FROM user WHERE role = 'user' AND created_at >= date('now')").fetchone()["count"]
    
    # Real data for General View Chart (Last 10 days)
    chart_data = conn.execute("""
        SELECT date(created_at) as join_date, COUNT(*) as count 
        FROM user 
        WHERE role = 'user' 
        GROUP BY join_date 
        ORDER BY join_date DESC 
        LIMIT 10
    """).fetchall()
    
    chart_labels = [row["join_date"] for row in reversed(chart_data)]
    chart_values = [row["count"] for row in reversed(chart_data)]
    
    # Ensure at least some data for visual consistency if empty
    if not chart_labels:
        chart_labels = ["No Data"]
        chart_values = [0]
    
    conn.close()

    companies = get_grouped_companies()
    
    notification_report = session.pop('last_notification_report', None)

    return render_template("admin/dashboard.html", 
                           username=session.get("username"),
                           users=users, 
                           companies=companies,
                           commission_ratio=commission_ratio,
                           total_users=total_users,
                           active_today=active_today,
                           chart_labels=chart_labels,
                           chart_values=chart_values,
                           notification_report=notification_report)

@admin.route("/update-ratio", methods=["POST"])
def update_ratio():
    if session.get("role") != "admin":
        return redirect(url_for("auth.login"))
    
    new_ratio = request.form.get("ratio")
    if new_ratio:
        conn = get_connection()
        conn.execute("INSERT OR REPLACE INTO global_settings (key, value) VALUES ('commission_ratio', ?)", (new_ratio,))
        conn.commit()
        conn.close()
        flash("Commission ratio updated successfully!", "success")
    
    return redirect(url_for("admin.dashboard"))

@admin.route("/add-company", methods=["POST"])
def add_company():
    if session.get("role") != "admin":
        return redirect(url_for("auth.login"))

    company_name = request.form.get("company_name")
    official_page_link = request.form.get("official_page_link")
    
    if not company_name or not official_page_link:
        flash("Company name and official link are required", "error")
        return redirect(url_for("admin.dashboard"))

    # Fetch jobs from API automatically using all roles users are interested in (new default)
    try:
        jobs = fetch_jobs(company_name)
    except Exception as e:
        print(f"Error fetching jobs: {e}")
        jobs = []

    conn = get_connection()
    
    if jobs:
        # Get current roles from API
        api_job_roles = {job["role"] for job in jobs}
        
        # Remove notifications for jobs that are about to be deleted
        conn.execute(
            "DELETE FROM notifications WHERE company_id IN (SELECT id FROM company WHERE company_name = ? AND job_role IS NOT NULL AND job_role NOT IN ({}))".format(
                ','.join(['?'] * len(api_job_roles))
            ),
            (company_name, *api_job_roles)
        )
        
        # Remove jobs from DB that are no longer in API results
        conn.execute(
            "DELETE FROM company WHERE company_name = ? AND job_role IS NOT NULL AND job_role NOT IN ({})".format(
                ','.join(['?'] * len(api_job_roles))
            ),
            (company_name, *api_job_roles)
        )
        
        new_jobs_count = 0
        for job in jobs:
            # Check if job already exists to avoid duplicates
            existing = conn.execute(
                "SELECT id FROM company WHERE company_name = ? AND job_role = ?",
                (company_name, job["role"])
            ).fetchone()
            
            if not existing:
                conn.execute(
                    "INSERT INTO company (company_name, official_page_link, job_role, start_date, end_date, location, job_level, experience_required, apply_link, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (company_name, official_page_link, job["role"], "Active", "TBD", job.get("location", "Remote"), job.get("level"), job.get("experience"), job.get("link"), 1 if job.get("active") else 0)
                )
                new_jobs_count += 1
            else:
                # Update existing job details
                conn.execute(
                    "UPDATE company SET job_level = ?, experience_required = ?, is_active = ?, location = ?, apply_link = ? WHERE id = ?",
                    (job.get("level"), job.get("experience"), 1 if job.get("active") else 0, job.get("location"), job.get("link"), existing["id"])
                )
        
        if new_jobs_count > 0:
            flash(f"Company added and {new_jobs_count} job roles synced!", "success")
        else:
            flash("Company updated and job roles synchronized", "info")
    else:
        # Remove notifications for all roles of this company
        conn.execute("DELETE FROM notifications WHERE company_id IN (SELECT id FROM company WHERE company_name = ? AND job_role IS NOT NULL)", (company_name,))
        
        # If no jobs found, remove any existing job roles for this company (as they are no longer active)
        conn.execute("DELETE FROM company WHERE company_name = ? AND job_role IS NOT NULL", (company_name,))
        
        # At least ensure the company existence entry (with no roles) remains or is created
        existing_comp = conn.execute("SELECT id FROM company WHERE company_name = ?", (company_name,)).fetchone()
        if not existing_comp:
            conn.execute(
                "INSERT INTO company (company_name, official_page_link) VALUES (?, ?)",
                (company_name, official_page_link)
            )
            flash("Company added but no active jobs found", "warning")
        else:
            flash("Company updated: all previous job roles removed as they are no longer active", "info")
        
    conn.commit()
    
    # Trigger notifications for all users for this specific company
    users = conn.execute("SELECT id FROM user WHERE role = 'user' AND email IS NOT NULL AND applied_job IS NOT NULL").fetchall()
    for u in users:
        check_and_notify_user(u["id"], conn)

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

@admin.route("/delete-entire-company/<string:company_name>", methods=["POST"])
def delete_entire_company(company_name):
    if session.get("role") != "admin":
        return redirect(url_for("auth.login"))
        
    conn = get_connection()
    conn.execute("DELETE FROM company WHERE company_name = ?", (company_name,))
    conn.commit()
    conn.close()
    flash(f"All records for {company_name} deleted successfully!", "success")
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
            # Now searching for all roles dynamically from database
            jobs = fetch_jobs(comp["company_name"])
            
            # Open a new connection for the updates
            conn = get_connection()
            
            # 1. Get current roles from API
            api_job_roles = {job["role"] for job in jobs}
            
            # 2. Get roles currently in DB for this company
            db_jobs = conn.execute(
                "SELECT id, job_role FROM company WHERE company_name = ? AND job_role IS NOT NULL",
                (comp["company_name"],)
            ).fetchall()
            
            # 3. Remove jobs from DB that are no longer in API results
            deleted_count = 0
            for db_job in db_jobs:
                if db_job["job_role"] not in api_job_roles:
                    # Remove notifications first
                    conn.execute("DELETE FROM notifications WHERE company_id = ?", (db_job["id"],))
                    # Remove the job
                    conn.execute("DELETE FROM company WHERE id = ?", (db_job["id"],))
                    deleted_count += 1
            
            # 4. Add new jobs or update existing ones
            for job in jobs:
                # Check if job already exists
                existing = conn.execute(
                    "SELECT id FROM company WHERE company_name = ? AND job_role = ?",
                    (comp["company_name"], job["role"])
                ).fetchone()
                
                if not existing:
                    conn.execute(
                        "INSERT INTO company (company_name, official_page_link, image_filename, job_role, start_date, end_date, location, job_level, experience_required, apply_link, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (comp["company_name"], comp["official_page_link"], comp["image_filename"], job["role"], "Active", "TBD", job.get("location", "Remote"), job.get("level"), job.get("experience"), job.get("link"), 1 if job.get("active") else 0)
                    )
                    sync_count += 1
                else:
                    # Update existing job details
                    conn.execute(
                        "UPDATE company SET job_level = ?, experience_required = ?, is_active = ?, location = ?, apply_link = ? WHERE id = ?",
                        (job.get("level"), job.get("experience"), 1 if job.get("active") else 0, job.get("location"), job.get("link"), existing["id"])
                    )
            
            conn.commit()
            
            if deleted_count > 0:
                print(f"Removed {deleted_count} stale jobs for {comp['company_name']}")
            
            # Trigger notifications for all users
            users = conn.execute("SELECT id FROM user WHERE role = 'user' AND email IS NOT NULL AND applied_job IS NOT NULL").fetchall()
            for u in users:
                check_and_notify_user(u["id"], conn)
                
            conn.close()
        except Exception as e:
            print(f"Error syncing {comp['company_name']}: {e}")
            continue

    flash(f"Synced {sync_count} new job roles and sent notifications!", "success")
    return redirect(url_for("admin.dashboard"))
import json

@admin.route("/admin/resume-templates")
def resume_templates():
    if session.get("role") != "admin":
        return redirect(url_for("auth.login"))
    
    conn = get_connection()
    templates = conn.execute("SELECT * FROM resume_templates").fetchall()
    conn.close()
    
    return render_template("admin/resume_templates.html", 
                           username=session.get("username"),
                           templates=templates)

@admin.route("/admin/add-resume-template", methods=["POST"])
def add_resume_template():
    if session.get("role") != "admin":
        return redirect(url_for("auth.login"))
    
    template_name = request.form.get("template_name")
    base_layout = request.form.get("base_layout", "marjorie")
    
    # Auto-generate a unique ID from the name
    template_id = template_name.lower().replace(" ", "_") + "_" + str(os.urandom(2).hex())
    
    image_file = request.files.get("resume_image")
    demo_data_str = request.form.get("demo_data", "").strip()
    
    try:
        if image_file and image_file.filename != '':
            # Analyze image to get JSON
            extracted_data = analyze_resume_image(image_file)
            if "error" in extracted_data:
                flash(f"Image analysis failed: {extracted_data['error']}", "error")
                return redirect(url_for("admin.resume_templates"))
            demo_data_str = json.dumps(extracted_data)
        elif not demo_data_str:
            flash("Either an image or manual JSON demo data is required.", "error")
            return redirect(url_for("admin.resume_templates"))
        
        # Validate final JSON
        json.loads(demo_data_str)
        
        conn = get_connection()
        conn.execute("INSERT INTO resume_templates (template_name, template_id, demo_data, base_layout) VALUES (?, ?, ?, ?)",
                     (template_name, template_id, demo_data_str, base_layout))
        conn.commit()
        conn.close()
        flash("Resume template added successfully with AI analysis!", "success")
    except Exception as e:
        flash(f"Error adding template: {e}", "error")
        
    return redirect(url_for("admin.resume_templates"))

@admin.route("/admin/toggle-template/<int:template_id>", methods=["POST"])
def toggle_template(template_id):
    if session.get("role") != "admin":
        return redirect(url_for("auth.login"))
        
    conn = get_connection()
    conn.execute("UPDATE resume_templates SET is_active = NOT is_active WHERE id = ?", (template_id,))
    conn.commit()
    conn.close()
    flash("Template status updated!", "success")
    return redirect(url_for("admin.resume_templates"))

@admin.route("/admin/delete-template/<int:template_id>", methods=["POST"])
def delete_resume_template(template_id):
    if session.get("role") != "admin":
        return redirect(url_for("auth.login"))
        
    conn = get_connection()
    conn.execute("DELETE FROM resume_templates WHERE id = ?", (template_id,))
    conn.commit()
    conn.close()
    flash("Template deleted successfully!", "success")
    return redirect(url_for("admin.resume_templates"))

@admin.route("/admin/analyze-resume-image", methods=["POST"])
def analyze_resume_image_route():
    if session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
        
    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    result = analyze_resume_image(image_file)
    return jsonify({"demo_data": result})
