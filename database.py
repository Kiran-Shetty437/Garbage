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

    try:
        c.execute("ALTER TABLE company ADD COLUMN last_sync TIMESTAMP")
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
        is_active INTEGER DEFAULT 1,
        last_sync TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        company_id INTEGER,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, company_id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS resume_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_name TEXT,
        template_id TEXT UNIQUE,
        demo_data TEXT,
        base_layout TEXT DEFAULT 'marjorie',
        is_active INTEGER DEFAULT 1
    )''')

    # Default Templates Initialization
    default_templates = [
        {
            "name": "Minimalist (Susanne)",
            "id": "susanne",
            "layout": "susanne",
            "data": {
                "personal": {
                    "fullName": "SUSANNE KINGSTON",
                    "phone": "Phone",
                    "email": "Email",
                    "location": "Address",
                    "linkedin": "LinkedIn Profile",
                    "twitter": "Twitter/Blog/Portfolio",
                    "summary": "To replace this text with your own, just click it and start typing. Briefly state your career objective, or summarize what makes you stand out. Use language from the job description as keywords."
                },
                "experience": [
                    {"role": "JOB TITLE", "company": "COMPANY", "duration": "DATES FROM - TO", "desc": "Describe your responsibilities and achievements in terms of impact and results. Use examples, but keep it short."},
                    {"role": "JOB TITLE", "company": "COMPANY", "duration": "DATES FROM - TO", "desc": "Describe your responsibilities and achievements in terms of impact and results. Use examples, but keep it short."}
                ],
                "education": [
                    {"degree": "DEGREE TITLE", "school": "SCHOOL", "year": "MONTH YEAR", "desc": "It's okay to brag about your GPA, awards, and honors. Feel free to summarize your coursework too."},
                    {"degree": "DEGREE TITLE", "school": "SCHOOL", "year": "MONTH YEAR", "desc": "It's okay to brag about your GPA, awards, and honors. Feel free to summarize your coursework too."}
                ],
                "skills": ["List your strengths relevant for the role you're applying for", "List one of your strengths", "List one of your strengths", "List one of your strengths", "List one of your strengths", "List one of your strengths"],
                "activities": ["Use this section to highlight your relevant passions, activities, and how you like to give back. It's good to include Leadership and volunteer experiences here. Or show off important extras like publications, certifications, languages and more."]
            }
        },
        {
            "name": "Classic (Marjorie)",
            "id": "marjorie",
            "layout": "marjorie",
            "data": {
                "personal": {
                    "fullName": "Marjorie D. McGahey",
                    "dob": "April 4, 1987",
                    "phone": "718-564-6972",
                    "email": "marjorie@jourrapide.com",
                    "location": "526 Longview Avenue, Brooklyn, NY 11226",
                    "summary": "Take advantages of sales skills & experience and understanding of tyres market to become a professional Sales Staff and bring a lot value to Customers. From that, I will contribute to development of your Company."
                },
                "education": [
                    {"school": "FOREIGN TRADE UNIVERSITY", "degree": "Economics and International Business\nGPA: 7.34/10", "year": "Sep 2005 - June 2015"}
                ],
                "experience": [
                    {"company": "UHE TRADING COMPANY", "role": "Sales Executive", "duration": "May 2011 - Now", "desc": "- Manage a retail shop in NeyOm province\n- Attend tyres exhibitions, conferences and meetings with suppliers"},
                    {"company": "CULTURIMEX BRANCH", "role": "Marketing Executive", "duration": "Apr 2010 - Apr 2011", "desc": "- Customer Care and look for new customers\n- Do marketing promotions for the image of the company\n- Implement the signed contract"}
                ],
                "activities": [
                    "VOLUNTEERING | New York | Jun 2008 - Mar 2009",
                    "- Belief Volunteers Group: Take care of and teach culture for the homeless children at Hanoi 3rd sponsor society Center.",
                    "- Cycling for Environment (C4E): cycling in every Sunday morning everyweek to propagandize people to protect our environment."
                ],
                "references": [
                    "Ms. C. Smith\nVice Director of Culturimex Branch\nAddress: 763 Elk Rd Little, Tucson, AZ 85705\nEmail: TyroneCSmith@teleworm.us\nMobile: 520-248-9575"
                ]
            }
        },
        {
            "name": "Modern (John)",
            "id": "john",
            "layout": "john",
            "data": {
                "personal": {
                    "fullName": "John Smith",
                    "professionalTitle": "IT Project Manager",
                    "phone": "774-987-4009",
                    "email": "j.smith@uptowork.com",
                    "linkedin": "linkedin.com/johnutw",
                    "twitter": "@johnsmithutw",
                    "summary": "IT Professional with over 10 years of experience specializing in IT department management for international logistics companies. I can implement effective IT strategies at local and global levels. My greatest strength is business awareness, which enables me to permanently streamline infrastructure and applications. Looking to leverage my IT Management skills at SanCorp Inc."
                },
                "experience": [
                    {"role": "Senior Project Manager", "company": "Seton Hospital, ME", "duration": "2006-12 - present", "desc": "• Oversaw all major hospital IT projects for 10+ years, focus on cost reduction.\n• Responsible for creating, improving, and developing IT project strategies.\n• Implemented the highly successful Lean Training and Six Sigma projects for all employees."},
                    {"role": "Junior Project Manager", "company": "Seton Hospital, ME", "duration": "2004-09 - 2006-12", "desc": "• Streamlined IT logistics and administration operation cutting costs by 25%\n• Diagnosed problems with hardware and operating systems and implemented solutions to increase efficiency.\n• Maintained the user database of over 30000 patients, implemented new solutions inside the dashboard."}
                ],
                "education": [
                    {"degree": "Master of Computer Science, University of Maryland", "school": "", "year": "1996-09 - 2001-05", "desc": "• Graduated Summa Cum Laude.\n• Andersen Postgraduate Fellowship to study advanced nursing techniques.\n• Managed a student project to develop a weekly nursing podcast."}
                ],
                "skills": [
                    "Business Process Improvement - history of successful innovations leading to cost savings",
                    "Vendor Management - proven track record of managing vendors in projects with budgets of over $1'000'000",
                    "Project Scheduling - over 90% of projects led were finished in due time",
                    "Sales Analysis - background in IT Sales with deep understanding of negotiating contracts"
                ],
                "software": [
                    {"name": "Microsoft Project", "level": "Excellent"},
                    {"name": "Microsoft Windows Server", "level": "Very Good"}
                ],
                "certifications": [
                    "2010-05 | PMP - Project Management Institute",
                    "2007-11 | CAPM - Project Management Institute"
                ]
            }
        },
        {
            "name": "Entry Level (Alex)",
            "id": "fresher1",
            "layout": "fresher1",
            "data": {
                "personal": {
                    "fullName": "ALEXANDER CHEN",
                    "email": "alex.chen@email.com",
                    "phone": "555-019-2831",
                    "location": "Seattle, WA",
                    "linkedin": "linkedin.com/in/alexc",
                    "summary": "Recent Computer Science graduate with a passion for frontend development and building accessible web applications. Adept at collaborating in team environments and quickly learning new technologies."
                },
                "education": [
                    {"degree": "B.S. Computer Science", "school": "University of Washington", "year": "May 2026", "desc": "GPA: 3.8/4.0\nRelevant Coursework: Web Development, Data Structures, Algorithms, Software Engineering"}
                ],
                "projects": [
                    {"name": "E-Commerce Mockup", "technologies": "React, Node.js, MongoDB", "link": "github.com/alexc/ecommerce", "desc": "Built a full-stack e-commerce application featuring user authentication, product catalog, and functional shopping cart.\nImplemented responsive design using Tailwind CSS."},
                    {"name": "Weather Dashboard", "technologies": "JavaScript, OpenWeather API", "link": "alexc.github.io/weather", "desc": "Developed a dynamic weather dashboard that fetches real-time forecast data via REST API.\nUtilized local storage to save user's searched cities."}
                ],
                "experience": [
                    {"role": "Software Engineering Intern", "company": "Tech Solutions Inc.", "duration": "Jun 2025 - Aug 2025", "desc": "Assisted in the development of internal dashboard tools using React.\nParticipated in daily stand-ups and code reviews."}
                ],
                "skills": ["JavaScript (ES6+)", "React.js", "HTML5 & CSS3", "Python", "Git & GitHub", "RESTful APIs"]
            }
        },
        {
            "name": "Creative Fresher (Sam)",
            "id": "fresher2",
            "layout": "fresher2",
            "data": {
                "personal": {
                    "fullName": "Samantha Lee",
                    "professionalTitle": "Entry Level Designer",
                    "email": "sam.lee@design.co",
                    "phone": "(555) 928-1120",
                    "location": "New York, NY",
                    "summary": "Creative and detail-oriented recent graduate with a BFA in Graphic Design. Excited to apply my theoretical knowledge and internship experience to create compelling visual narratives."
                },
                "education": [
                    {"degree": "BFA Graphic Design", "school": "Parsons School of Design", "year": "2022 - 2026", "desc": "Dean's List 2024, 2025\nCapstone Project: 'Reimagining Urban Spaces'"}
                ],
                "projects": [
                    {"name": "Brand Identity Redesign", "technologies": "Illustrator, InDesign", "link": "Behance/samleedesign", "desc": "Created a comprehensive brand identity for a local coffee shop including logo, packaging, and social media templates."},
                    {"name": "UI/UX App Concept", "technologies": "Figma", "link": "Dribbble/samleedesign", "desc": "Designed user interfaces for a plant care mobile app, focusing on accessibility and intuitive navigation."}
                ],
                "skills": ["Adobe Creative Suite", "Figma", "Typography", "Color Theory", "Prototyping", "Illustration"],
                "activities": ["Design Club Vice President", "Volunteer at Local Art Workshop"]
            }
        }
    ]

    import json
    for t in default_templates:
        c.execute("INSERT OR IGNORE INTO resume_templates (template_name, template_id, demo_data, base_layout) VALUES (?, ?, ?, ?)",
                  (t["name"], t["id"], json.dumps(t["data"]), t["layout"]))

    conn.commit()
    conn.close()