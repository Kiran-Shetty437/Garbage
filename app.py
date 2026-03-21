from flask import Flask
import os

from config import SECRET_KEY, UPLOAD_FOLDER
from database import init_db

from routes.auth_routes import auth
from routes.admin_routes import admin
from routes.user_routes import user


app = Flask(__name__)

app.secret_key = SECRET_KEY

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


init_db()


app.register_blueprint(auth)
app.register_blueprint(admin)
app.register_blueprint(user)

# Automatic Sync System (Daily) - Native Threading Implementation
from services.job_service import sync_all_companies
import threading
import time

def start_background_sync():
    def run_sync_loop():
        # Initial wait for the server to be ready
        time.sleep(15)
        while True:
            try:
                print("Starting automatic daily job sync...")
                sync_all_companies()
                print("Daily job sync completed successfully.")
            except Exception as e:
                print(f"Error in automatic background sync: {e}")
            
            # Wait 24 hours (86400 seconds)
            time.sleep(86400)

    thread = threading.Thread(target=run_sync_loop, daemon=True)
    thread.start()

# Only start sync in the main process (avoiding issues with Flask reloader)
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    try:
        start_background_sync()
    except Exception as e:
        print(f"Warning: Could not start background sync: {e}")


if __name__ == "__main__":
    app.run(debug=True)