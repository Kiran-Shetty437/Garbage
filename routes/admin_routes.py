from flask import Blueprint, render_template, session, redirect, url_for, request, flash, current_app, jsonify

from database import get_connection
import os
from werkzeug.utils import secure_filename
from services.job_service import fetch_jobs, sync_all_companies, sync_company_jobs, check_and_notify_user
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
                "last_sync": row["last_sync"],
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

    company_names_str = request.form.get("company_name")
    official_page_link = request.form.get("official_page_link")
    
    if not company_names_str or not official_page_link:
        flash("Company name(s) and official link are required", "error")
        return redirect(url_for("admin.dashboard"))

    # Support multiple companies comma-separated
    company_names = [c.strip() for c in company_names_str.split(',') if c.strip()]
    
    total_new_jobs = 0
    synced_companies = []

    for company_name in company_names:
        new_jobs = sync_company_jobs(company_name, official_page_link)
        total_new_jobs += new_jobs
        synced_companies.append(company_name)

    if len(company_names) > 1:
        flash(f"Processed {len(company_names)} companies. Found {total_new_jobs} new job roles total.", "success")
    else:
        if total_new_jobs > 0:
            flash(f"Company '{company_names[0]}' added/updated with {total_new_jobs} new roles!", "success")
        else:
            flash(f"Company '{company_names[0]}' processed.", "info")
    
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
        
    try:
        new_roles = sync_all_companies()
        flash(f"Sync complete! Found {new_roles} new job roles and sent notifications.", "success")
    except Exception as e:
        flash(f"Error during sync: {e}", "error")

    return redirect(url_for("admin.dashboard"))


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


