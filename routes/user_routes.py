from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify
from database import get_connection
import os
from werkzeug.utils import secure_filename
from services.chatbot_service import job_chatbot
from routes.admin_routes import check_and_notify_user
from services.resume_service import analyze_resume, extract_pdf_text, extract_docx_text
from services.aptitude_service import generate_aptitude_questions
import re

user = Blueprint("user", __name__)

def validate_password(password):
    if not (8 <= len(password) <= 12):
        return False, "Password must be between 8 and 12 characters."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one capital letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one small letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[@$!%*?&#]", password):
        return False, "Password must contain at least one special character (@$!%*?&#)."
    return True, ""



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
        action = request.form.get("action", "change_password")
        
        if action == "update_notifications":
            enabled = 1 if request.form.get("notifications_enabled") == "on" else 0
            conn = get_connection()
            conn.execute("UPDATE user SET notifications_enabled=? WHERE id=?", (enabled, session["user_id"]))
            conn.commit()
            conn.close()
            flash("Notification preferences updated!", "success")
            return redirect(url_for("user.profile"))

        if action == "update_roles":
            applied_jobs = request.form.getlist("applied_job")
            jobs_str = ", ".join([job.strip() for job in applied_jobs if job.strip()])
            
            if not jobs_str:
                flash("You must have at least one target job role.", "error")
                return redirect(url_for("user.profile"))
                
            conn = get_connection()
            conn.execute("UPDATE user SET applied_job=? WHERE id=?", (jobs_str, session["user_id"]))
            conn.commit()
            conn.close()
            
            try:
                check_and_notify_user(session["user_id"])
            except Exception as e:
                print(f"Notification error: {e}")
                
            flash("Target job roles updated successfully!", "success")
            return redirect(url_for("user.profile"))

        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if new_password != confirm_password:
            flash("New passwords do not match.", "error")
        else:
            is_valid, msg = validate_password(new_password)
            if not is_valid:
                flash(msg, "error")
                return redirect(url_for("user.profile"))
                
            conn = get_connection()
            user_row = conn.execute("SELECT password FROM user WHERE id=?", (session["user_id"],)).fetchone()

            if user_row and user_row["password"] == current_password:
                conn.execute("UPDATE user SET password=? WHERE id=?", (new_password, session["user_id"]))
                conn.commit()
                flash("Password updated successfully!", "success")
            else:
                flash("Incorrect current password.", "error")
            conn.close()

    return redirect(url_for("user.profile"))




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

    # Filter out companies with 0 jobs for the USER view
    final_companies = [c for c in companies_dict.values() if len(c["jobs"]) > 0]

    return render_template("user/dashboard.html", 
                           username=session.get("username"),
                           companies=final_companies)


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
import json

@user.route("/resume_builder")
def resume_builder():
    if session.get("role") != "user":
        return redirect(url_for("auth.login"))
    
    conn = get_connection()
    templates_rows = conn.execute("SELECT * FROM resume_templates WHERE is_active = 1").fetchall()
    conn.close()
    
    templates = []
    for row in templates_rows:
        try:
            demo_data = json.loads(row["demo_data"])
            templates.append({
                "id": row["id"],
                "name": row["template_name"],
                "templateId": row["template_id"],
                "baseLayout": row["base_layout"],
                "demo": demo_data
            })
        except:
            continue

    return render_template("user/resume_builder.html", 
                           username=session.get("username"),
                           dynamic_templates=templates)

@user.route("/aptitude", methods=["GET"])
def aptitude():
    if session.get("role") != "user":
        return redirect(url_for("auth.login"))
    
    conn = get_connection()
    patterns = conn.execute("SELECT company_name FROM aptitude_patterns").fetchall()
    conn.close()
    
    return render_template("user/aptitude_portal.html", 
                           username=session.get("username"), 
                           patterns=patterns)

@user.route("/aptitude/generate_json", methods=["POST"])
def generate_aptitude_json():
    if session.get("role") != "user":
        return jsonify({"error": "Unauthorized"}), 403
        
    data = request.json
    company_name = data.get("company_name")
    difficulty = data.get("difficulty")
    
    conn = get_connection()
    pattern_row = conn.execute("SELECT patterns_json FROM aptitude_patterns WHERE company_name=?", (company_name,)).fetchone()
    conn.close()
    
    if not pattern_row:
        return jsonify({"error": "Pattern not found"}), 404
        
    # Build test questions using Gemini
    generated_test = generate_aptitude_questions(company_name, difficulty, pattern_row["patterns_json"])
    
    if not generated_test:
        return jsonify({"error": "Generation failed"}), 500
        
    # Calculate total minutes and attach them to each section
    sections_pattern = json.loads(pattern_row["patterns_json"])
    total_minutes = 0
    
    for gen_sec in generated_test:
        # Find matching pattern entry to get minutes
        match = next((s for s in sections_pattern if s.get('section', '').lower() == gen_sec.get('section', '').lower()), None)
        mins = int(match.get('minutes', 5)) if match else 5
        gen_sec['minutes'] = mins
        total_minutes += mins
    
    # Store test info in session
    session["aptitude_test"] = {
        "company_name": company_name,
        "difficulty": difficulty,
        "data": generated_test,
        "total_minutes": total_minutes
    }
    
    return jsonify({
        "questions": generated_test,
        "total_minutes": total_minutes,
        "company_name": company_name,
        "difficulty": difficulty
    })

@user.route("/aptitude/submit_json", methods=["POST"])
def submit_aptitude_json():
    if session.get("role") != "user":
        return jsonify({"error": "Unauthorized"}), 403
        
    test_info = session.get("aptitude_test")
    if not test_info:
        return jsonify({"error": "Session expired"}), 400
        
    user_answers = request.json.get("answers", {})
    score = 0
    total = 0
    question_index = 0
    
    sections_results = []
    
    for section in test_info["data"]:
        section_score = 0
        section_total = 0
        section_questions = []
        
        for q in section["questions"]:
            user_ans_idx = user_answers.get(str(question_index))
            is_correct = False
            if user_ans_idx is not None and str(user_ans_idx) == str(q.get("correct_index")):
                score += 1
                section_score += 1
                is_correct = True
            
            section_questions.append({
                "text": q.get("text"),
                "options": q.get("options"),
                "user_answer": user_ans_idx,
                "correct_index": q.get("correct_index"),
                "is_correct": is_correct
            })
            
            total += 1
            section_total += 1
            question_index += 1
            
        sections_results.append({
            "section_name": section.get("section", "General"),
            "score": section_score,
            "total": section_total,
            "questions": section_questions
        })
            
    percentage = int((score / total) * 100) if total > 0 else 0
    
    # Clear test session
    session.pop("aptitude_test", None)
    
    return jsonify({
        "score": score,
        "total": total,
        "percentage": percentage,
        "company_name": test_info["company_name"],
        "difficulty": test_info["difficulty"],
        "sections_results": sections_results
    })
