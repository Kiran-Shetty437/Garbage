from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from database import get_connection

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
            conn.close()

            if user:
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["role"] = "user"
                
                # Check if profile is complete
                if not user["email"] or not user["resume_filename"]:
                    return redirect(url_for("user.user_details"))
                
                return redirect(url_for("user.dashboard"))
            else:
                flash("Invalid credentials", "error")
                return render_template("login.html")

        elif action == "signup":
            conn = get_connection()
            try:
                conn.execute(
                    "INSERT INTO user (username, password, role) VALUES (?, ?, ?)",
                    (username, password, "user")
                )
                conn.commit()
                flash("Signup successful! Please login.", "success")
            except Exception as e:
                flash("Username already exists", "error")
            finally:
                conn.close()
            return render_template("login.html")

    return render_template("login.html")



@auth.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("auth.login"))