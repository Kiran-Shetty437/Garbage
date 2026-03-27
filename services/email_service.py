import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD, BASE_URL


def send_job_alert(user_email, username, company, role, link, notification_id):

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = user_email
    msg["Subject"] = f"Job Alert: {role} at {company}"

    # Tracking link
    tracking_link = f"{BASE_URL}/notification/view/{notification_id}?redirect={link}"

    body = f"""
Hi {username}

New job found!

Company: {company}
Role: {role}

Apply here:
{tracking_link}
"""

    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()

        return True

    except Exception as e:
        print(f"SMTP Error: {e}")
        return False


def send_otp_email(user_email, otp):
    msg = MIMEMultipart()
    msg["From"] = f"CareerConnect <{SENDER_EMAIL}>"
    msg["To"] = user_email
    msg["Subject"] = "Password Reset OTP"

    body = f"""
Hi,

Your OTP for password reset is: {otp}

Please enter this OTP to reset your password.
"""
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending OTP: {e}")
        return False