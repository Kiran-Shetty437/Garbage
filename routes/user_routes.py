from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify
from database import get_connection
import os
from werkzeug.utils import secure_filename
from services.chatbot_service import job_chatbot
from routes.admin_routes import check_and_notify_user
from services.resume_service import analyze_resume, extract_pdf_text, extract_docx_text

user = Blueprint("user", __name__)


@user.route("/profile")
def profile():
    if session.get("role") != "user":
        return redirect(url_for("auth.login"))

    conn = get_connection()
    user_row = conn.execute("SELECT * FROM user WHERE id=?", (session["user_id"],)).fetchone()
    resume_row = conn.execute("SELECT * FROM resume_data WHERE user_id=?", (session["user_id"],)).fetchone()
    conn.close()

    if not user_row:
        flash("User not found!", "error")
        return redirect(url_for("auth.login"))

    return render_template("user/profile.html", user=user_row, resume_data=resume_row)


@user.route("/settings", methods=["GET", "POST"])
def settings():
    if session.get("role") != "user":
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if new_password != confirm_password:
            flash("New passwords do not match.", "error")
        else:
            conn = get_connection()
            user_row = conn.execute("SELECT password FROM user WHERE id=?", (session["user_id"],)).fetchone()

            if user_row and user_row["password"] == current_password:
                conn.execute("UPDATE user SET password=? WHERE id=?", (new_password, session["user_id"]))
                conn.commit()
                flash("Password updated successfully!", "success")
            else:
                flash("Incorrect current password.", "error")
            conn.close()

    return render_template("user/settings.html", username=session.get("username"))




@user.route("/user")
@user.route("/user/dashboard")
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
                "location": row["location"],
                "level": row["job_level"],
                "experience": row["experience_required"],
                "active": row["is_active"],
                "apply_link": row["apply_link"] or row["official_page_link"] or "#"
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

        # Trigger automatic notification check for this user
        check_and_notify_user(session["user_id"])

        flash("Profile updated successfully!", "success")
        return redirect(url_for("user.dashboard"))

    conn = get_connection()
    user_data = conn.execute("SELECT email FROM user WHERE id=?", (session["user_id"],)).fetchone()
    conn.close()

    return render_template("user/details.html", username=session.get("username"), email=user_data["email"])




@user.route("/chat", methods=["POST"])
def chat():
    if session.get("role") != "user":
        return jsonify({"reply": "Unauthorized access."}), 403
    
    data = request.json
    user_input = data.get("message")
    
    if not user_input:
        return jsonify({"reply": "No input provided."}), 400

    reply = job_chatbot(user_input)
    return jsonify({"reply": reply})


@user.route("/analyze_resume", methods=["POST"])
def analyze():
    if session.get("role") != "user":
        return jsonify({"result": "Unauthorized access."}), 403
    
    file = request.files.get("resume")

    if not file or file.filename == "":
        return jsonify({"result": "⚠️ Please upload your resume (PDF or Word file) to analyze."}), 400

    if file.filename.endswith(".pdf"):
        text = extract_pdf_text(file)
    elif file.filename.endswith(".docx"):
        text = extract_docx_text(file)
    else:
        return jsonify({"result": "⚠️ Only PDF or Word (.docx) files are supported."}), 400

    if not text.strip():
        return jsonify({"result": "⚠️ Could not extract text from the file."}), 400

    result = analyze_resume(text)
    return jsonify({"result": result})
