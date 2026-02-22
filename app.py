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


if __name__ == "__main__":
    app.run(debug=True)