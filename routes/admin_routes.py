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
    active_today = conn.execute("SELECT COUNT(*) as count FROM user WHERE role = 'user' AND date(last_activity) = date('now')").fetchone()["count"]

    # Calculate avg screen time
    avg_row = conn.execute("SELECT AVG(total_screen_time) as avg_time FROM user WHERE role = 'user'").fetchone()
    avg_minutes = avg_row["avg_time"] if avg_row["avg_time"] and avg_row["avg_time"] is not None else 0
    avg_h = int(avg_minutes // 60)
    avg_m = int(avg_minutes % 60)
    avg_screen_time = f"{avg_h}h {avg_m}m"
    
    # Real data for General View Chart (Last 10 days)
    # We'll generate the last 10 days to ensure the chart shows the timeline even with holes
    from datetime import datetime, timedelta
    today = datetime.now()
    dates = [(today - timedelta(days=i)).date().isoformat() for i in range(9, -1, -1)]
    
    chart_data_map = {d: 0 for d in dates}
    
    db_chart_data = conn.execute("""
        SELECT date(created_at) as join_date, COUNT(*) as count 
        FROM user 
        WHERE role = 'user' AND created_at >= ?
        GROUP BY join_date 
    """, (dates[0],)).fetchall()
    
    for row in db_chart_data:
        if row["join_date"] in chart_data_map:
            chart_data_map[row["join_date"]] = row["count"]
            
    chart_labels = dates
    chart_values = [chart_data_map[d] for d in dates]
    
    companies = get_grouped_companies()
    
    apt_patterns_raw = conn.execute("SELECT * FROM aptitude_patterns ORDER BY created_at DESC").fetchall()
    import json
    aptitude_patterns = []
    for r in apt_patterns_raw:
        aptitude_patterns.append({
            "id": r["id"],
            "company_name": r["company_name"],
            "patterns": json.loads(r["patterns_json"]) if r["patterns_json"] else []
        })
        
    templates = conn.execute("SELECT * FROM resume_templates").fetchall()
    conn.close()
    
    notification_report = session.pop('last_notification_report', None)

    return render_template("admin/dashboard.html", 
                           username=session.get("username"),
                           users=users, 
                           companies=companies,
                           aptitude_patterns=aptitude_patterns,
                           templates=templates,
                           commission_ratio=commission_ratio,
                           total_users=total_users,
                           active_today=active_today,
                           avg_screen_time=avg_screen_time,
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



@admin.route("/admin/notification-report")
def notification_report():
    if session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
        
    conn = get_connection()
    # Join notifications with user to get names
    reports = conn.execute("""
        SELECT n.*, u.username, u.email 
        FROM notifications n
        JOIN user u ON n.user_id = u.id
        ORDER BY n.sent_at DESC
    """).fetchall()
    conn.close()
    
    return jsonify([dict(r) for r in reports])


@admin.route("/admin/toggle-template/<int:template_id>", methods=["POST"])
def toggle_template(template_id):
    if session.get("role") != "admin":
        return redirect(url_for("auth.login"))
        
    conn = get_connection()
    conn.execute("UPDATE resume_templates SET is_active = NOT is_active WHERE id = ?", (template_id,))
    conn.commit()
    conn.close()
    flash("Template status updated!", "success")
    return redirect(url_for("admin.dashboard") + "?view=templates")

@admin.route("/admin/delete-template/<int:template_id>", methods=["POST"])
def delete_resume_template(template_id):
    if session.get("role") != "admin":
        return redirect(url_for("auth.login"))
        
    conn = get_connection()
    conn.execute("DELETE FROM resume_templates WHERE id = ?", (template_id,))
    conn.commit()
    conn.close()
    flash("Template deleted successfully!", "success")
    return redirect(url_for("admin.dashboard") + "?view=templates")


@admin.route("/admin/add-aptitude", methods=["POST"])
def add_aptitude():
    if session.get("role") != "admin":
        return redirect(url_for("auth.login"))
        
    company_name = request.form.get("company_name")
    
    # Collect dynamic sections
    section_names = request.form.getlist("section_name[]")
    questions = request.form.getlist("questions[]")
    minutes = request.form.getlist("minutes[]")
    
    patterns = []
    for name, q, m in zip(section_names, questions, minutes):
        if name.strip():
            patterns.append({
                "section": name.strip(),
                "questions": int(q) if q.isdigit() else 0,
                "minutes": int(m) if m.isdigit() else 0
            })
            
    if company_name and patterns:
        import json
        import sqlite3
        conn = get_connection()
        try:
            conn.execute("INSERT INTO aptitude_patterns (company_name, patterns_json) VALUES (?, ?) ON CONFLICT(company_name) DO UPDATE SET patterns_json=excluded.patterns_json",
                         (company_name.strip(), json.dumps(patterns)))
            conn.commit()
            flash(f"Aptitude pattern for {company_name} added/updated!", "success")
        except sqlite3.Error as e:
            flash(f"Error saving pattern: {e}", "error")
        finally:
            conn.close()
    else:
        flash("Company name and at least one pattern section are required.", "error")
            
    return redirect(url_for("admin.dashboard") + "?view=aptitude")


@admin.route("/admin/delete-aptitude/<int:pattern_id>", methods=["POST"])
def delete_aptitude(pattern_id):
    if session.get("role") != "admin":
        return redirect(url_for("auth.login"))
        
    conn = get_connection()
    conn.execute("DELETE FROM aptitude_patterns WHERE id = ?", (pattern_id,))
    conn.commit()
    conn.close()
    flash("Aptitude pattern deleted successfully!", "success")
    return redirect(url_for("admin.dashboard") + "?view=aptitude")

@admin.route("/admin/chart-data")
def chart_data():
    if session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
        
    timeframe = request.args.get("timeframe", "10days")
    metric = request.args.get("metric", "users")
    conn = get_connection()
    from datetime import datetime, timedelta
    from dateutil.relativedelta import relativedelta
    import calendar
    
    today = datetime.now()
    datasets = []
    labels = []
    
    # Configure Metric
    if metric == "active":
        date_col = "last_activity"
        agg_func = "COUNT(*)"
        label_postfix = " Active"
        main_color = "#00d2ff"
        main_bg = "rgba(0, 210, 255, 0.2)"
    elif metric == "screen_time":
        date_col = "last_activity"
        agg_func = "AVG(total_screen_time)"
        label_postfix = " Avg Screen Time"
        main_color = "#7b61ff"
        main_bg = "rgba(123, 97, 255, 0.2)"
    else:  # "users" default
        date_col = "created_at"
        agg_func = "COUNT(*)"
        label_postfix = " Users"
        main_color = "#10b981"
        main_bg = "rgba(16, 185, 129, 0.2)"
        
    prev_color = "#8b96c9"
    prev_bg = "rgba(139, 150, 201, 0.2)"
    
    # Helper to fetch and map data
    def get_query_counts(dates, is_month_group=False, max_len=None):
        if is_month_group:
            start_iso = datetime(dates[0].year, 1, 1).date().isoformat()
            end_iso = datetime(dates[-1].year + 1, 1, 1).date().isoformat()
            group_col = f"strftime('%Y-%m', {date_col})"
            date_map = {f"{m.year}-{m.month:02d}": 0 for m in dates}
        else:
            start_iso = dates[0].isoformat()
            end_iso = (dates[-1] + timedelta(days=1)).isoformat()
            group_col = f"date({date_col})"
            date_map = {d.isoformat(): 0 for d in dates}
            
        data = conn.execute(f"""
            SELECT {group_col} as g_date, {agg_func} as count 
            FROM user WHERE role = 'user' AND {date_col} IS NOT NULL 
                AND {date_col} >= ? AND {date_col} < ?
            GROUP BY g_date
        """, (start_iso, end_iso)).fetchall()
        
        for r in data:
            if r["g_date"] in date_map:
                val = r["count"]
                if val is not None and metric == "screen_time":
                    val = round(float(val), 1)
                date_map[r["g_date"]] = val or 0
                
        if is_month_group:
            result = [date_map[f"{m.year}-{m.month:02d}"] for m in dates]
        else:
            result = [date_map[d.isoformat()] for d in dates]
            
        if max_len is not None:
            while len(result) < max_len:
                result.append(None)
        return result

    if timeframe == "week":
        # Current Week vs Previous Week
        current_dates = [(today - timedelta(days=i)).date() for i in range(6, -1, -1)]
        prev_dates = [(today - timedelta(days=i)).date() for i in range(13, 6, -1)]
        
        labels = [d.strftime("%a") for d in current_dates]
        
        datasets = [
            {"label": "This Week", "data": get_query_counts(current_dates), "borderColor": main_color, "backgroundColor": main_bg, "tension": 0.4, "fill": True},
            {"label": "Last Week", "data": get_query_counts(prev_dates), "borderColor": prev_color, "backgroundColor": prev_bg, "tension": 0.4, "fill": True}
        ]
        
    elif timeframe == "month":
        # Current Calendar Month vs Previous Calendar Month
        this_month_start = datetime(today.year, today.month, 1).date()
        if today.month == 12:
            this_month_end = datetime(today.year + 1, 1, 1).date()
        else:
            this_month_end = datetime(today.year, today.month + 1, 1).date()
            
        this_month_name = calendar.month_name[today.month]
        this_month_days = (this_month_end - this_month_start).days
        current_dates = [this_month_start + timedelta(days=i) for i in range(this_month_days)]
        
        prev_month_dt = today - relativedelta(months=1)
        prev_month_start = datetime(prev_month_dt.year, prev_month_dt.month, 1).date()
        if prev_month_dt.month == 12:
            prev_month_end = datetime(prev_month_dt.year + 1, 1, 1).date()
        else:
            prev_month_end = datetime(prev_month_dt.year, prev_month_dt.month + 1, 1).date()
            
        prev_month_name = calendar.month_name[prev_month_dt.month]
        prev_month_days = (prev_month_end - prev_month_start).days
        prev_dates = [prev_month_start + timedelta(days=i) for i in range(prev_month_days)]
        
        max_days = max(this_month_days, prev_month_days)
        labels = [str(i+1) for i in range(max_days)]
        
        datasets = [
            {"label": this_month_name, "data": get_query_counts(current_dates, False, max_days), "borderColor": main_color, "backgroundColor": main_bg, "tension": 0.4, "fill": True},
            {"label": prev_month_name, "data": get_query_counts(prev_dates, False, max_days), "borderColor": prev_color, "backgroundColor": prev_bg, "tension": 0.4, "fill": True}
        ]
        
    elif timeframe == "year":
        # Current Calendar Year vs Previous Calendar Year
        this_year = today.year
        prev_year = today.year - 1
        
        labels = [calendar.month_abbr[i] for i in range(1, 13)]
        
        current_months_dt = [datetime(this_year, i, 1).date() for i in range(1, 13)]
        prev_months_dt = [datetime(prev_year, i, 1).date() for i in range(1, 13)]
        
        datasets = [
            {"label": str(this_year), "data": get_query_counts(current_months_dt, True), "borderColor": main_color, "backgroundColor": main_bg, "tension": 0.4, "fill": True},
            {"label": str(prev_year), "data": get_query_counts(prev_months_dt, True), "borderColor": prev_color, "backgroundColor": prev_bg, "tension": 0.4, "fill": True}
        ]
        
    else:
        # Default 10 days
        dates = [(today - timedelta(days=i)).date() for i in range(9, -1, -1)]
        labels = [d.isoformat() for d in dates]
        datasets = [
            {"label": f"Last 10 Days{label_postfix}", "data": get_query_counts(dates), "borderColor": main_color, "backgroundColor": main_bg, "tension": 0.4, "fill": True}
        ]

    conn.close()
    return jsonify({"labels": labels, "datasets": datasets})
