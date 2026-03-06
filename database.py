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
        applied_job TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_screen_time INTEGER DEFAULT 0
    )''')

    try:
        # Note: SQLite 3 cannot use CURRENT_TIMESTAMP as a default when using ALTER TABLE.
        # Fixed by using a constant string as the default.
        c.execute("ALTER TABLE user ADD COLUMN created_at TIMESTAMP DEFAULT '2024-01-01 00:00:00'")
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("ALTER TABLE user ADD COLUMN total_screen_time INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    c.execute('''CREATE TABLE IF NOT EXISTS global_settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')

    # Default ratio value
    c.execute("INSERT OR IGNORE INTO global_settings (key, value) VALUES ('commission_ratio', '10.0')")

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
        location TEXT,
        job_level TEXT,
        experience_required TEXT,
        apply_link TEXT,
        is_active INTEGER DEFAULT 1
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