from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from database import get_connection
import random
import time
from services.email_service import send_otp_email

auth = Blueprint("auth", __name__)

# Hardcoded admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


@auth.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        action = request.form.get("action", "login")
        username = request.form["username"]
        password = request.form["password"]

        if action == "login":
            # ✅ ADMIN LOGIN CHECK
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                session["username"] = username
                session["role"] = "admin"
                return redirect(url_for("admin.dashboard"))

            # ✅ USER LOGIN CHECK
            conn = get_connection()
            user = conn.execute(
                "SELECT * FROM user WHERE username=? AND password=?",
                (username, password)
            ).fetchone()
            if user:
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["role"] = "user"
                session["login_time"] = time.time()
                
                # Check if profile is complete
                if not user["email"] or not user["resume_filename"]:
                    conn.close()
                    return redirect(url_for("user.user_details"))
                
                conn.close()
                return redirect(url_for("user.dashboard"))
            else:
                conn.close()
                flash("Invalid credentials", "error")
                return render_template("login.html")

        elif action == "signup":
            email = request.form.get("email")
            conn = get_connection()
            
            # 🛡️ DUPLICATE EMAIL CHECK (During Signup)
            existing_email = conn.execute("SELECT * FROM user WHERE email=?", (email,)).fetchone()
            if existing_email:
                conn.close()
                flash("Signup failed: This email is already registered with another account.", "error")
                return render_template("login.html")

            try:
                conn.execute(
                    "INSERT INTO user (username, password, role, email) VALUES (?, ?, ?, ?)",
                    (username, password, "user", email)
                )
                conn.commit()
                flash("Signup successful! Please login.", "success")
            except Exception as e:
                flash("Username already exists", "error")
            finally:
                conn.close()
            return render_template("login.html")

    return render_template("login.html")



@auth.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        conn = get_connection()
        user = conn.execute("SELECT * FROM user WHERE email=?", (email,)).fetchone()
        conn.close()

        if user:
            otp = random.randint(100000, 999999)
            session["otp"] = str(otp)
            session["reset_email"] = email
            if send_otp_email(email, otp):
                flash("OTP sent to your email.", "success")
                return render_template("verify_otp.html")
            else:
                flash("Failed to send OTP. Please try again.", "error")
        else:
            flash("No account associated with this email.", "error")

    return render_template("forgot_password.html")


@auth.route("/verify-otp", methods=["POST"])
def verify_otp():
    user_otp = request.form["otp"]
    saved_otp = session.get("otp")

    if user_otp == saved_otp:
        # User is "allowed" to reset their password
        return render_template("reset_password.html")
    else:
        flash("Invalid OTP. Please try again.", "error")
        return render_template("verify_otp.html")


@auth.route("/reset-password", methods=["POST"])
def reset_password():
    new_password = request.form["password"]
    email = session.get("reset_email")

    if email:
        conn = get_connection()
        conn.execute("UPDATE user SET password=? WHERE email=?", (new_password, email))
        conn.commit()
        conn.close()
        session.pop("otp", None)
        session.pop("reset_email", None)
        flash("Password reset successful. Please login.", "success")
        return redirect(url_for("auth.login"))
    else:
        flash("Invalid session.", "error")
        return redirect(url_for("auth.login"))


@auth.route("/logout")
def logout():
    user_id = session.get("user_id")
    login_time = session.get("login_time")
    
    if user_id and login_time:
        # Calculate session duration in minutes (at least 1 minute if they logged in)
        duration = int((time.time() - login_time) / 60) + 1
        conn = get_connection()
        conn.execute("UPDATE user SET total_screen_time = total_screen_time + ? WHERE id = ?", (duration, user_id))
        conn.commit()
        conn.close()

    session.clear()
    return redirect(url_for("auth.login"))