from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from database import get_connection
import random
import time
from services.email_service import send_otp_email

auth = Blueprint("auth", __name__)

# Hardcoded admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


@auth.route("/login", methods=["GET", "POST"])
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
                # Update last activity
                conn.execute("UPDATE user SET last_activity = CURRENT_TIMESTAMP WHERE id = ?", (user["id"],))
                conn.commit()

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
                return render_template("login.html", state="login")

        elif action == "signup":
            email = request.form.get("email").strip().lower()
            conn = get_connection()
            
            # 🛡️ DUPLICATE EMAIL CHECK (During Signup)
            existing_email = conn.execute("SELECT * FROM user WHERE LOWER(email)=?", (email,)).fetchone()
            if existing_email:
                conn.close()
                flash("Signup failed: This email is already registered with another account.", "error")
                return render_template("login.html", state="signup")

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
            return render_template("login.html", state="login")

    return render_template("login.html", state="login")


@auth.route("/signup")
def signup():
    return render_template("login.html", state="signup")



@auth.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email_input = request.form.get("email", "").strip().lower()
        if not email_input:
            flash("Please enter an email address.", "error")
            return redirect(url_for("auth.login"))
            
        conn = get_connection()
        user = conn.execute("SELECT * FROM user WHERE LOWER(email)=?", (email_input,)).fetchone()
        conn.close()

        if user:
            otp = random.randint(100000, 999999)
            session["otp"] = str(otp)
            session["reset_email"] = email_input
            if send_otp_email(email_input, otp):
                flash("OTP sent to your email.", "success")
                return render_template("login.html", state="verify")
            else:
                flash("Failed to send OTP. Please try again.", "error")
        else:
            flash("No account associated with this email.", "error")
        
        return redirect(url_for("auth.login"))

    return render_template("login.html")


@auth.route("/verify-otp", methods=["POST"])
def verify_otp():
    user_otp = request.form["otp"]
    saved_otp = session.get("otp")

    if user_otp == saved_otp:
        # User is "allowed" to reset their password
        return render_template("login.html", state="reset")
    else:
        flash("Invalid OTP. Please try again.", "error")
        return render_template("login.html", state="verify")


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


@auth.route("/notification/view/<int:notification_id>")
def view_notification(notification_id):
    redirect_url = request.args.get("redirect", url_for("auth.login"))
    
    conn = get_connection()
    try:
        conn.execute("UPDATE notifications SET is_seen = 1 WHERE id = ?", (notification_id,))
        conn.commit()
    except Exception as e:
        print(f"Error updating notification: {e}")
    finally:
        conn.close()
        
    return redirect(redirect_url)


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