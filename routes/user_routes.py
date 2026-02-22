from flask import Blueprint, render_template, session, redirect, url_for
from database import get_connection

user = Blueprint("user", __name__)


@user.route("/user")
def dashboard():
    if session.get("role") != "user":
        return redirect(url_for("auth.login"))

    conn = get_connection()
    rows = conn.execute("SELECT * FROM company").fetchall()
    conn.close()

    # Grouping logic
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
        
        if row["job_role"]:
            companies_dict[name]["jobs"].append({
                "job_role": row["job_role"],
                "start_date": row["start_date"],
                "end_date": row["end_date"],
                "location": row["location"]
            })

    return render_template("user/dashboard.html", 
                           username=session.get("username"),
                           companies=list(companies_dict.values()))
