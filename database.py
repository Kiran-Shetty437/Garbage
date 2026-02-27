import sqlite3
from config import DB_NAME

def get_connection():
    conn = sqlite3.connect(DB_NAME, timeout=20)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT,
        email TEXT,
        resume_filename TEXT,
        applied_job TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS resume_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        full_name TEXT,
        phone TEXT,
        location TEXT,
        linkedin TEXT,
        github TEXT,
        skills TEXT,
        education TEXT,
        experience TEXT,
        projects TEXT,
        summary TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS company (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT,
        official_page_link TEXT,
        image_filename TEXT,
        job_role TEXT,
        start_date TEXT,
        end_date TEXT,
        location TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        company_id INTEGER,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, company_id)
    )''')

    conn.commit()
    conn.close()