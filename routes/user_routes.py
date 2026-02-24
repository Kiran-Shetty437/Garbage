from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from database import get_connection
import os
from werkzeug.utils import secure_filename

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


@user.route("/details", methods=["GET", "POST"])
def user_details():
    if session.get("role") != "user":
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        email = request.form.get("email")
        applied_jobs = request.form.getlist("applied_job")
        resume = request.files.get("resume")

        if not email or not applied_jobs or not resume:
            flash("All fields are required!", "error")
            return redirect(url_for("user.user_details"))

        # Save resume
        filename = secure_filename(f"{session['username']}_{resume.filename}")
        upload_path = os.path.join("static", "uploads", filename)
        
        # Ensure directory exists (though app.py does it)
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        resume.save(upload_path)

        # Store jobs as comma separated string
        jobs_str = ", ".join(applied_jobs)

        # Update user in database
        conn = get_connection()
        conn.execute(
            "UPDATE user SET email=?, resume_filename=?, applied_job=? WHERE id=?",
            (email, filename, jobs_str, session["user_id"])
        )
        conn.commit()
        conn.close()

        flash("Profile updated successfully!", "success")
        return redirect(url_for("user.dashboard"))

    return render_template("user/details.html", username=session.get("username"))
