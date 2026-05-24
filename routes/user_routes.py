from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify
from database import get_connection
import os
import re
from config import UPLOAD_FOLDER
from werkzeug.utils import secure_filename
from services.chatbot_service import job_chatbot
from routes.admin_routes import check_and_notify_user
from services.resume_service import analyze_resume, extract_pdf_text, extract_docx_text, extract_resume_info
from services.aptitude_service import generate_aptitude_questions

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

def allowed_file(filename, allowed_extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions

RESUME_EXTENSIONS = {"pdf", "doc", "docx"}
IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

@user.route("/user")
@user.route("/user/dashboard")
def dashboard():
    if session.get("role") != "user":
        return redirect(url_for("auth.login"))

    conn = get_connection()
    rows = conn.execute("SELECT * FROM company").fetchall()
    user_row = conn.execute("SELECT profile_pic FROM user WHERE id=?", (session["user_id"],)).fetchone()
    conn.close()

    profile_pic = user_row["profile_pic"] if user_row else None

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
        
        if row["job_role"] and row["is_active"] == 1:
            companies_dict[name]["jobs"].append({
                "job_role": row["job_role"],
                "start_date": row["start_date"],
                "end_date": row["end_date"],
                "location": row["location"],
                "level": row["job_level"],
                "experience": row["experience_required"],
                "apply_link": row["apply_link"],
                "is_active": row["is_active"]
            })
    
    return render_template("user/dashboard.html", companies=list(companies_dict.values()), user_id=session["user_id"], username=session.get("username"), profile_pic=profile_pic)

@user.route("/profile/update", methods=["POST"])
def update_profile():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))
    
    user_id = session["user_id"]
    conn = get_connection()
    
    # Handle Profile Pic
    if 'profile_pic' in request.files:
        file = request.files['profile_pic']
        if file and file.filename:
            if not allowed_file(file.filename, IMAGE_EXTENSIONS):
                flash("Invalid image format for profile picture. Use PNG, JPG, or GIF.", "error")
            else:
                filename = secure_filename(f"profile_{user_id}_{file.filename}")
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                conn.execute("UPDATE user SET profile_pic = ? WHERE id = ?", (filename, user_id))

    # Handle Resume Upload
    if 'resume' in request.files:
        file = request.files['resume']
        if file and file.filename:
            if not allowed_file(file.filename, RESUME_EXTENSIONS):
                flash("Invalid resume format. Please use PDF or DOC/DOCX.", "error")
            else:
                filename = secure_filename(f"resume_{user_id}_{file.filename}")
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                conn.execute("UPDATE user SET resume_filename = ? WHERE id = ?", (filename, user_id))
    
    # Handle other fields
    job_roles = request.form.getlist("job_role_item")
    applied_job = ",".join([j.strip() for j in job_roles if j.strip()])
    
    experience_level = request.form.get("experience_level")
    location = request.form.get("location")
    skills = request.form.get("skills")
    
    notifications_enabled = 1 if request.form.get("notifications_enabled") else 0
    
    conn.execute("""
        UPDATE user 
        SET applied_job = ?, experience_level = ?, location = ?, skills = ?, notifications_enabled = ?
        WHERE id = ?
    """, (applied_job, experience_level, location, skills, notifications_enabled, user_id))
    
    conn.commit()
    conn.close()
    
    flash("Profile updated successfully!", "success")
    return redirect(url_for("user.profile"))

@user.route("/profile/resume/delete")
def delete_resume():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))
    
    user_id = session["user_id"]
    conn = get_connection()
    user_row = conn.execute("SELECT resume_filename FROM user WHERE id = ?", (user_id,)).fetchone()
    
    if user_row and user_row['resume_filename']:
        try:
            file_path = os.path.join(UPLOAD_FOLDER, user_row['resume_filename'])
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting resume file: {e}")
            
        conn.execute("UPDATE user SET resume_filename = NULL WHERE id = ?", (user_id,))
        conn.commit()
        flash("Resume deleted successfully.", "success")
    else:
        flash("No resume found to delete.", "error")
        
    conn.close()
    return redirect(url_for("user.profile"))

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


@user.route("/chat", methods=["GET", "POST"])
def chat():
    if session.get("role") != "user":
        return redirect(url_for("auth.login"))
    
    if request.method == "POST":
        user_msg = request.json.get("message")
        if not user_msg:
            return jsonify({"error": "Empty message"})
            
        bot_response = job_chatbot(user_msg)
        return jsonify({"reply": bot_response})
        
    return render_template("user/chatbot.html")


@user.route("/resume/analyze", methods=["GET", "POST"])
def resume_analysis():
    if session.get("role") != "user":
        return redirect(url_for("auth.login"))

    analysis_result = None
    if request.method == "POST":
        file = request.files.get("resume")
        if not file:
            flash("No file uploaded", "error")
        else:
            if not allowed_file(file.filename, RESUME_EXTENSIONS):
                flash("Unsupported file format. Please upload PDF or DOC/DOCX only.", "error")
                return redirect(url_for("user.resume_analysis"))
            
            file_ext = os.path.splitext(file.filename)[1].lower()
            text = ""
            if file_ext == ".pdf":
                text = extract_pdf_text(file)
            elif file_ext in [".doc", ".docx"]:
                text = extract_docx_text(file)

            if text:
                analysis_result = analyze_resume(text)
                
                # Update user profile with extracted info
                extracted_info = extract_resume_info(text)
                if extracted_info:
                    conn = get_connection()
                    
                    # Update resume_data table
                    conn.execute("""
                        INSERT OR REPLACE INTO resume_data 
                        (user_id, full_name, phone, location, linkedin, github, instagram, website, skills, summary)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        session["user_id"],
                        extracted_info.get("full_name"),
                        extracted_info.get("phone"),
                        extracted_info.get("location"),
                        extracted_info.get("linkedin"),
                        extracted_info.get("github"),
                        extracted_info.get("instagram"),
                        extracted_info.get("website"),
                        extracted_info.get("skills"),
                        extracted_info.get("summary")
                    ))
                    
                    # Also update user table roles if they are empty
                    current_user = conn.execute("SELECT applied_job FROM user WHERE id=?", (session["user_id"],)).fetchone()
                    if not current_user["applied_job"]:
                         conn.execute("UPDATE user SET applied_job = ? WHERE id = ?", (extracted_info.get("skills", ""), session["user_id"]))
                    
                    conn.commit()
                    conn.close()

    return render_template("user/resume_analysis.html", analysis_result=analysis_result)

from flask import jsonify

@user.route("/api/analyze_resume", methods=["POST"])
def api_analyze_resume():
    if session.get("role") != "user":
        return jsonify({"error": "Unauthorized"}), 401

    file = request.files.get("resume")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    file_ext = os.path.splitext(file.filename)[1].lower()
    if not allowed_file(file.filename, RESUME_EXTENSIONS):
        return jsonify({"error": "Unsupported format. Please upload PDF or DOC/DOCX only."}), 400
        
    text = ""
    try:
        if file_ext == ".pdf":
            text = extract_pdf_text(file)
        elif file_ext in [".doc", ".docx"]:
            text = extract_docx_text(file)
    except Exception as e:
        return jsonify({"error": f"Failed to extract document text: {str(e)}"}), 500

    if not text:
         return jsonify({"error": "Could not extract text from the document"}), 400

    try:
        analysis_result = analyze_resume(text)
        return jsonify({"result": analysis_result})
    except Exception as e:
        return jsonify({"error": f"AI Engine failed to analyze: {str(e)}"}), 500


@user.route("/aptitude")
def aptitude():
    if session.get("role") != "user":
        return redirect(url_for("auth.login"))
    
    conn = get_connection()
    patterns = conn.execute("SELECT DISTINCT company_name FROM aptitude_patterns").fetchall()
    # Also get default patterns from questions if patterns table is empty
    if not patterns:
        patterns = conn.execute("SELECT DISTINCT company_name FROM aptitude_questions").fetchall()
    user_row = conn.execute("SELECT username, profile_pic FROM user WHERE id=?", (session["user_id"],)).fetchone()
    conn.close()

    username = user_row["username"] if user_row else session.get("username")
    profile_pic = user_row["profile_pic"] if user_row else None
    
    return render_template("user/aptitude_portal.html", patterns=patterns, username=username, profile_pic=profile_pic)


@user.route("/aptitude/generate_json", methods=["POST"])
def generate_test_json():
    if not session.get("user_id"):
        return jsonify({"error": "Auth required"}), 401
        
    data = request.json
    company_name = data.get("company_name", "").strip()
    difficulty = data.get("difficulty", "medium").strip()
    
    try:
        conn = get_connection()
        pattern_row = conn.execute("SELECT patterns_json FROM aptitude_patterns WHERE UPPER(company_name) = UPPER(?)", (company_name,)).fetchone()
        conn.close()
        
        if not pattern_row:
             # Default pattern if not found
             import json as pyjson
             pattern_json = pyjson.dumps([{"section": "General Aptitude", "questions": 10, "minutes": 10}])
        else:
             pattern_json = pattern_row["patterns_json"]

        test_data = generate_aptitude_questions(company_name, difficulty, pattern_json)
        if not test_data:
            return jsonify({"error": "Failed to generate questions"}), 500
        
        # Add IDs to questions for the frontend
        q_id = 1
        for section in test_data:
            for q in section.get("questions", []):
                q["id"] = q_id
                q_id += 1

        return jsonify({
            "company_name": company_name,
            "difficulty": difficulty,
            "questions": test_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@user.route("/aptitude/submit_json", methods=["POST"])
def submit_test_json():
    if not session.get("user_id"):
        return jsonify({"error": "Auth required"}), 401
        
    data = request.json
    
    total = 0
    score = 0
    sections_results = []

    for section in data.get("questions", []):
        sec_total = len(section.get("questions", []))
        sec_score = 0
        q_results = []
        
        for q in section.get("questions", []):
            total += 1
            user_ans = data.get("answers", {}).get(str(q["id"]))
            is_correct = str(user_ans) == str(q["correct_index"])
            if is_correct:
                score += 1
                sec_score += 1
            
            q_results.append({
                "id": q["id"],
                "text": q["text"],
                "options": q["options"],
                "correct_index": q["correct_index"],
                "user_answer": user_ans,
                "is_correct": is_correct
            })
            
        sections_results.append({
            "section_name": section.get("section"),
            "score": sec_score,
            "total": sec_total,
            "questions": q_results
        })
        
    percentage = (score / total * 100) if total > 0 else 0
    
    return jsonify({
        "score": score,
        "total": total,
        "percentage": round(percentage, 1),
        "company_name": data.get("company_name"),
        "difficulty": data.get("difficulty"),
        "sections_results": sections_results
    })


@user.route("/resume/builder", methods=["GET", "POST"])
def resume_builder():
    if session.get("role") != "user":
        return redirect(url_for("auth.login"))

    conn = get_connection()
    templates = conn.execute("SELECT * FROM resume_templates WHERE is_active = 1").fetchall()
    
    # Simple templates mapping
    dynamic_templates = []
    for t in templates:
        try:
             import json as pyjson
             demo_data = pyjson.loads(t['demo_data']) if t['demo_data'] else {}
             dynamic_templates.append({
                "templateId": t['template_id'] or str(t['id']),
                "name": t['template_name'],
                "demo": demo_data,
                "baseLayout": t['base_layout']
            })
        except:
            continue

    user_data = conn.execute("SELECT * FROM user WHERE id=?", (session["user_id"],)).fetchone()
    resume_data = conn.execute("SELECT * FROM resume_data WHERE user_id=?", (session["user_id"],)).fetchone()
    conn.close()

    return render_template("user/resume_builder.html", 
                         dynamic_templates=dynamic_templates,
                         user=user_data,
                         resume_data=resume_data)


@user.route("/heartbeat", methods=["POST"])
def heartbeat():
    if not session.get("user_id"):
        return jsonify({"status": "ignored"}), 200
    
    user_id = session["user_id"]
    conn = get_connection()
    # Increment total_screen_time by 1 minute and update last_activity
    conn.execute("""
        UPDATE user 
        SET total_screen_time = total_screen_time + 1,
            last_activity = datetime('now')
        WHERE id = ?
    """, (user_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "okay"}), 200
