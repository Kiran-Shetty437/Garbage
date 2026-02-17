from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'super_secret_key'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DB_NAME = 'users.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
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
                    summary TEXT,
                    FOREIGN KEY(user_id) REFERENCES user(id)
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS company (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL,
                    official_page_link TEXT NOT NULL
                )''')

    # Migrations
    cols = {
        'user': ['email', 'resume_filename', 'applied_job'],
        'resume_data': ['full_name', 'phone', 'location', 'linkedin', 'github', 'projects', 'summary'],
        'company': ['company_name', 'official_page_link']
    }
    for table, columns in cols.items():
        for col in columns:
            try:
                c.execute(f"ALTER TABLE {table} ADD COLUMN {col} TEXT")
            except sqlite3.OperationalError:
                pass 


    conn.commit()
    conn.close()

init_db()

# Hardcoded Admin Credentials (Dictionary)
ADMIN_CREDENTIALS = {
    'username': 'admin',
    'password': 'admin123'
}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        action = request.form.get('action')
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        if action == 'signup':
            role = 'user'
            try:
                if username == ADMIN_CREDENTIALS['username']:
                     flash('Username already exists.', 'error')
                else:
                    c.execute("INSERT INTO user (username, password, role) VALUES (?, ?, ?)", (username, password, role))
                    conn.commit()
                    flash('Signup successful! Please login.', 'success')
            except sqlite3.IntegrityError:
                flash('Username already exists.', 'error')
            finally:
                conn.close()
            return redirect(url_for('index'))

        elif action == 'login':
            if username == ADMIN_CREDENTIALS['username'] and password == ADMIN_CREDENTIALS['password']:
                session['user_id'] = 'admin'
                session['username'] = username
                session['role'] = 'admin'
                conn.close()
                return redirect(url_for('admin_dashboard'))

            c.execute("SELECT * FROM user WHERE username = ? AND password = ?", (username, password))
            user = c.fetchone()
            conn.close()

            if user:
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['role'] = user[3]
                
                # Check if profile is complete (email is present)
                if user[4]: 
                    return redirect(url_for('user_dashboard'))
                
                # If incomplete, redirect to details page
                return redirect(url_for('user_details'))
            else:
                flash('Invalid credentials.', 'error')
                return redirect(url_for('index'))
    
    return render_template('login.html')

import re
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

# ... (imports) ...

def extract_resume_data(filepath):
    """
    Enhanced AI-powered extraction logic.
    """
    text = ""
    if filepath.lower().endswith('.pdf'):
        if not PyPDF2:
            return {"error": "PyPDF2 not installed"}
        try:
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return {}
    
    # AI Analysis Logic
    data = {
        'full_name': None,
        'email': None,
        'phone': None,
        'location': None,
        'linkedin': None,
        'github': None,
        'skills': [],
        'education': [],
        'experience': [],
        'projects': [],
        'summary': None
    }
    
    lower_text = text.lower()
    lines = text.split('\n')

    # 1. Name Extraction (Heuristic: First line usually has name)
    if lines:
        data['full_name'] = lines[0].strip()

    # 2. Extract Links (LinkedIn / GitHub)
    li_match = re.search(r'linkedin\.com/in/[\w-]+', lower_text)
    if li_match: data['linkedin'] = li_match.group(0)
    
    gh_match = re.search(r'github\.com/[\w-]+', lower_text)
    if gh_match: data['github'] = gh_match.group(0)

    # 3. Extract Email & Phone
    email_match = re.search(r'[\w\.-]+@[\w\.-]+', text)
    if email_match: data['email'] = email_match.group(0)

    phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    if phone_match: data['phone'] = phone_match.group(0)

    # 4. Extract Location (Heuristic: City, State pattern)
    loc_match = re.search(r'([A-Z][a-z]+(?: [A-Z][a-z]+)*),? [A-Z]{2}', text)
    if loc_match: data['location'] = loc_match.group(0)
        
    # 5. Extract Skills
    common_skills = ['python', 'java', 'javascript', 'html', 'css', 'react', 'flask', 'sql', 'mysql', 'c++', 'c#', 
                     'aws', 'azure', 'docker', 'kubernetes', 'git', 'agile', 'machine learning', 'ai', 'data analysis']
    found_skills = set()
    for skill in common_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', lower_text):
            found_skills.add(skill.title())
    data['skills'] = list(found_skills)
    
    # 6. Extract Education
    education_keywords = ['bachelor', 'master', 'phd', 'degree', 'university', 'college', 'bs', 'ms']
    edu_lines = [line.strip() for line in lines if any(kw in line.lower() for kw in education_keywords)]
    data['education'] = edu_lines[:3]
    
    # 7. Extract Summary & Projects (Heuristic based on keywords)
    summary_idx = lower_text.find('summary')
    if summary_idx != -1:
        data['summary'] = text[summary_idx+7:summary_idx+300].strip().split('\n')[0]

    project_idx = lower_text.find('projects')
    if project_idx != -1:
        data['projects'] = [text[project_idx+8:project_idx+400].strip()]

    return data

@app.route('/user/details', methods=['GET', 'POST'])
def user_details():
    if 'user_id' not in session or session.get('role') != 'user':
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        applied_job = request.form.get('applied_job')
        resume_file = request.files['resume']
        
        filename = None
        analyzed_data = {}
        
        if resume_file:
            filename = secure_filename(resume_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            resume_file.save(filepath)
            analyzed_data = extract_resume_data(filepath)
            if not email and analyzed_data.get('email'):
                email = analyzed_data['email']
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE user SET email = ?, resume_filename = ?, applied_job = ? WHERE id = ?", 
                  (email, filename, applied_job, session['user_id']))
        
        # Store metadata
        c.execute("SELECT id FROM resume_data WHERE user_id = ?", (session['user_id'],))
        if c.fetchone():
             c.execute('''UPDATE resume_data SET full_name=?, phone=?, location=?, linkedin=?, github=?, 
                        skills=?, education=?, experience=?, projects=?, summary=? WHERE user_id=?''', 
                       (analyzed_data.get('full_name'), analyzed_data.get('phone'), analyzed_data.get('location'),
                        analyzed_data.get('linkedin'), analyzed_data.get('github'), 
                        ", ".join(analyzed_data.get('skills', [])), "; ".join(analyzed_data.get('education', [])),
                        "; ".join(analyzed_data.get('experience', [])), "; ".join(analyzed_data.get('projects', [])),
                        analyzed_data.get('summary'), session['user_id']))
        else:
             c.execute('''INSERT INTO resume_data (user_id, full_name, phone, location, linkedin, github, 
                        skills, education, experience, projects, summary) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                       (session['user_id'], analyzed_data.get('full_name'), analyzed_data.get('phone'), 
                        analyzed_data.get('location'), analyzed_data.get('linkedin'), analyzed_data.get('github'),
                        ", ".join(analyzed_data.get('skills', [])), "; ".join(analyzed_data.get('education', [])),
                        "; ".join(analyzed_data.get('experience', [])), "; ".join(analyzed_data.get('projects', [])),
                        analyzed_data.get('summary')))

        conn.commit()
        conn.close()
        flash('Profile updated and Jobs applied successfully!', 'success')
        return redirect(url_for('user_dashboard'))

    return render_template('user/details.html', username=session.get('username'))

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('index'))
    
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Allow accessing columns by name
    c = conn.cursor()
    
    # Fetch users with their resume skills if available
    # Left join to get all users even if no resume data
    query = '''
        SELECT u.id, u.username, u.email, u.applied_job, r.skills 
        FROM user u 
        LEFT JOIN resume_data r ON u.id = r.user_id
        WHERE u.role != 'admin'
    '''
    c.execute(query)
    users = c.fetchall()
    # Fetch companies
    c.execute("SELECT * FROM company")
    companies = c.fetchall()
    
    conn.close()
    
    return render_template('admin/dashboard.html', username=session['username'], users=users, companies=companies)

@app.route('/admin/add_company', methods=['POST'])
def add_company():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('index'))
    
    company_name = request.form.get('company_name')
    official_link = request.form.get('official_link')
    
    if company_name and official_link:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO company (company_name, official_page_link) VALUES (?, ?)", (company_name, official_link))
        conn.commit()
        conn.close()
        flash('Company added successfully!', 'success')
    else:
        flash('Please fill in all fields.', 'error')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_company/<int:company_id>', methods=['POST'])
def delete_company(company_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('index'))
        
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM company WHERE id = ?", (company_id,))
    conn.commit()
    conn.close()
    flash('Company deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('index'))
        
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Optional: Delete uploaded resume file?
    # First get filename
    c.execute("SELECT resume_filename FROM user WHERE id = ?", (user_id,))
    user = c.fetchone()
    if user and user[0]:
        try:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], user[0])
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")

    try:
        # Delete from resume_data first (foreign key)
        c.execute("DELETE FROM resume_data WHERE user_id = ?", (user_id,))
        # Delete from user table
        c.execute("DELETE FROM user WHERE id = ?", (user_id,))
        conn.commit()
        flash('User deleted successfully.', 'success')
    except Exception as e:
        flash(f'Error deleting user: {e}', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('admin_dashboard'))

@app.route('/user')
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
        
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        # Fetch latest user data
        c.execute("SELECT * FROM user WHERE id = ?", (session['user_id'],))
        user = c.fetchone()
        
        if not user:
            # This could happen if admin (id='admin') accesses this route
            # or if a user was deleted.
            conn.close()
            if session.get('role') == 'admin':
                return redirect(url_for('admin_dashboard'))
            session.clear()
            return redirect(url_for('index'))

        # Fetch analyzed resume data
        c.execute("SELECT * FROM resume_data WHERE user_id = ?", (session['user_id'],))
        resume_data = c.fetchone()
        
        return render_template('user/dashboard.html', 
                               username=user['username'], 
                               email=user['email'], 
                               applied_job=user['applied_job'],
                               resume=user['resume_filename'], 
                               analyzed_info=resume_data)
    finally:
        conn.close()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
