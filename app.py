from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from werkzeug.utils import secure_filename

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

# GLOBAL JOB ROLES LIST
JOB_ROLES = [

    # Software Development
    "Software Engineer",
    "Software Developer",
    "Python Developer",
    "Java Developer",
    "C++ Developer",
    "C# Developer",
    "Javascript Developer",
    "Full Stack Developer",
    "Frontend Developer",
    "Backend Developer",
    "Web Developer",

    # Data & AI
    "Data Scientist",
    "Data Analyst",
    "Machine Learning Engineer",
    "AI Engineer",
    "Deep Learning Engineer",
    "NLP Engineer",

    # Cloud & DevOps
    "DevOps Engineer",
    "Cloud Engineer",
    "AWS Engineer",
    "Azure Engineer",

    # Mobile
    "Android Developer",
    "iOS Developer",
    "Flutter Developer",

    # Testing
    "QA Engineer",
    "Software Tester",
    "Automation Tester",

    # Fresher roles
    "Intern",
    "Software Engineer Intern",
    "Graduate Engineer Trainee",
    "Trainee Engineer"
]


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
                    official_page_link TEXT NOT NULL,
                    image_filename TEXT,
                    job_role TEXT,
                    start_date TEXT,
                    end_date TEXT
                )''')

    # Migrations
    cols = {
        'user': ['email', 'resume_filename', 'applied_job'],
        'resume_data': ['full_name', 'phone', 'location', 'linkedin', 'github', 'projects', 'summary'],
        'company': ['company_name', 'official_page_link', 'image_filename', 'job_role', 'start_date', 'end_date']
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

import requests
from bs4 import BeautifulSoup

def scrape_job_details(url):
    """
    Enhanced Scraper: Supports JSON-LD (schema.org) common in enterprise sites (Microsoft, etc.)
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return None, "N/A", "N/A"
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        found_role = None
        start_date = "N/A"
        end_date = "N/A"

        # 1. Try JSON-LD (Best for Microsoft, LinkedIn, Google Careers)
        json_ld = soup.find_all('script', type='application/ld+json')
        for script in json_ld:
            try:
                data = json.loads(script.string)
                # JobPosting schema
                if isinstance(data, dict):
                    if data.get('@type') == 'JobPosting' or 'title' in data:
                        found_role = data.get('title')
                        start_date = data.get('datePosted', "N/A")
                        # Some use validThrough for end date
                        end_date = data.get('validThrough', "N/A")
                        break
                elif isinstance(data, list):
                    for item in data:
                        if item.get('@type') == 'JobPosting':
                            found_role = item.get('title')
                            start_date = item.get('datePosted', "N/A")
                            end_date = item.get('validThrough', "N/A")
                            break
            except:
                continue

        # 2. Fallback to Meta Tags if JSON-LD failed
        if not found_role:
            meta_role = soup.find('meta', property='og:title') or \
                       soup.find('meta', attrs={'name': 'twitter:title'})
            if meta_role and meta_role.get('content'):
                found_role = meta_role['content'].split('|')[0].split('-')[0].strip()

        # 3. Fallback to Heuristics/Text Search
        if not found_role:
            text = soup.get_text(separator=' ').strip()
            roles = JOB_ROLES

            for r in roles:
                if re.search(r'\b' + re.escape(r) + r'\b', text, re.I):
                    found_role = r
                    break
        
        # Date Cleanup
        if start_date != "N/A":
             # Try to format date if it looks like YYYY-MM-DD
             match = re.search(r'\d{4}-\d{2}-\d{2}', str(start_date))
             if match: start_date = match.group(0)

        if end_date == "N/A":
            import datetime
            now = datetime.datetime.now()
            start_date = now.strftime("%Y-%m-%d") if start_date == "N/A" else start_date
            end_date = (now + datetime.timedelta(days=30)).strftime("%Y-%m-%d")

        return found_role or "General Opening", start_date, end_date
    except Exception as e:
        print(f"Scraping error: {e}")
        return "Unknown Role", "N/A", "N/A"

def job_matches(user_interest, job_role):
    """
    Improved matching logic without changing old logic structure
    """

    if not user_interest or not job_role:
        return False

    user_interest = user_interest.lower().strip()
    job_role = job_role.lower().strip()

    # exact match
    if user_interest == job_role:
        return True

    # contains match
    if user_interest in job_role or job_role in user_interest:
        return True

    # word match
    user_words = user_interest.split()
    role_words = job_role.split()

    for word in user_words:
        if word in role_words:
            return True

    return False



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
        # Handle multiple jobs
        applied_jobs_list = request.form.getlist('applied_job')
        applied_job = ", ".join([job.strip() for job in applied_jobs_list if job.strip()])
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
    image_file = request.files.get('company_image')

    manual_role = request.form.get('manual_role')
    manual_start = request.form.get('manual_start')
    manual_end = request.form.get('manual_end')

    filename = None

    if image_file and image_file.filename != '':
        filename = secure_filename(image_file.filename)
        image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    if company_name and official_link:

        scraped_role, s_date, e_date = scrape_job_details(official_link)

        final_role = manual_role if manual_role else scraped_role
        final_start = manual_start if manual_start else s_date
        final_end = manual_end if manual_end else e_date

        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute('''
            INSERT INTO company
            (company_name, official_page_link, image_filename, job_role, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (company_name, official_link, filename, final_role, final_start, final_end))

        conn.commit()

        # NOTIFY USERS AUTOMATICALLY
        c.execute("SELECT username, email, applied_job FROM user WHERE role != 'admin'")
        users = c.fetchall()

        for user in users:

            if not user['email'] or not user['applied_job']:
                continue

            interests = [j.strip() for j in user['applied_job'].split(",")]

            for interest in interests:

                if job_matches(interest, final_role):

                    send_job_alert(
                        user['email'],
                        user['username'],
                        company_name,
                        final_role,
                        official_link
                    )

                    break

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

        # Fetch all companies
        c.execute("SELECT * FROM company")
        companies = c.fetchall()
        
        return render_template('user/dashboard.html', 
                               username=user['username'], 
                               email=user['email'], 
                               applied_job=user['applied_job'],
                               resume=user['resume_filename'], 
                               analyzed_info=resume_data,
                               companies=companies)
    finally:
        conn.close()

@app.route('/admin/sync_all_jobs', methods=['POST'])
def sync_all_jobs():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('index'))
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, official_page_link FROM company")
    companies = c.fetchall()
    
    sync_count = 0
    for cid, link in companies:
        role, s_date, e_date = scrape_job_details(link)
        if role:
            c.execute("UPDATE company SET job_role = ?, start_date = ?, end_date = ? WHERE id = ?", 
                      (role, s_date, e_date, cid))
            sync_count += 1
            
    conn.commit()
    conn.close()
    flash(f'Successfully re-scraped and synced {sync_count} companies.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def send_job_alert(user_email, username, company_name, job_role, link):
    """
    Sends an email alert to the user using SMTP.
    Note: You need to configure valid SMTP credentials here.
    """
    # SMTP Config (Example for Gmail)
    # FOR USER: Replace these with your actual credentials or use environment variables
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SENDER_EMAIL = "abc387029@gmail.com" # REPLACE THIS
    SENDER_PASSWORD = "kaqowqwhvbcdqmdw" # REPLACE THIS

    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["To"] = user_email
    message["Subject"] = f"Job Alert: New {job_role} opening at {company_name}!"

    body = f"""
    Hi {username},

    We found a job opening that matches your interest!

    Company: {company_name}
    Role: {job_role}
    
    You can check more details here: {link}

    Good luck with your application!
    """
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            # server.login(SENDER_EMAIL, SENDER_PASSWORD) # Uncomment and set credentials
            # server.sendmail(SENDER_EMAIL, user_email, message.as_string())
            print(f"DEBUG: Email alert would be sent to {user_email} for {job_role} at {company_name}")
            return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@app.route('/admin/notify_users', methods=['POST'])
def notify_users():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('index'))
    
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT id, username, email, applied_job FROM user WHERE role != 'admin'")
    users = c.fetchall()
    
    c.execute("SELECT company_name, job_role, official_page_link FROM company")
    companies = c.fetchall()
    
    conn.close()
    
    notifications_sent = 0
    for user in users:
        if not user['email'] or not user['applied_job']:
            continue
            
        user_interests = [j.strip().lower() for j in user['applied_job'].split(',')]
        
        for company in companies:
            if not company['job_role']:
                continue
                
            scraped_role = company['job_role'].lower()
            
            # Simple match: if scraped role contains any user interest or vice versa
            matched = False
            for interest in user_interests:
                if job_matches(interest, company['job_role']):
                    matched = True
                    break
            
            if matched:
                if send_job_alert(user['email'], user['username'], company['company_name'], company['job_role'], company['official_page_link']):
                    notifications_sent += 1
    
    if notifications_sent > 0:
        flash(f'Notifications processed! {notifications_sent} potential matches found/notified (Check console logs for simulation).', 'success')
    else:
        flash('No new matches found to notify.', 'info')
        
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
