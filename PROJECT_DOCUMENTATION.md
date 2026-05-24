# CareerConnect - Project Documentation

## 1. Project Overview
**CareerConnect** is a comprehensive job portal and professional development platform designed to bridge the gap between job seekers and companies. It features automated job synchronization, AI-powered resume analysis, a dynamic resume builder, and an interactive aptitude testing portal.

---

## 2. Technology Stack
- **Backend Framework**: Flask (Python)
- **Architecture**: Blueprint-based modular structure
- **Database**: SQLite (Native `sqlite3` with row factory)
- **Services**:
  - **Job Synchronization**: Automated API-based fetching and syncing of company job boards.
  - **Email System**: Custom SMTP integration for job alerts and OTPs.
  - **Resume Parsing**: PDF and DOCX text extraction using `services/resume_service`.
  - **AI Integration**: Chatbot for career guidance and resume analysis.
- **Frontend**:
  - **Layout**: Jinja2 templates with a professional CSS design system.
  - **Interactivity**: Dynamic forms, AJAX-based chatbot, and real-time test generation.

---

## 3. System Requirements Specification (SRS)

### 3.1 Role-Based Features
#### **Admin Role**
- **Dashboard**: Real-time stats on user activity, screen time, and registration trends.
- **Job Management**: Add companies by URL, trigger manual or automatic job syncs, and delete job roles.
- **User Management**: Monitor and manage registered users.
- **Resource Management**: Manage resume templates and aptitude test patterns.
- **Revenue Control**: Set and update commission ratios for the platform.

#### **User Role**
- **Dashboard**: View personalized job listings grouped by company.
- **Profile Management**: Option to upload resumes and select dream roles to enhance job matching.
- **Resume Builder**: Create professional resumes using dynamic templates and custom layouts.
- **AI Chatbot**: Get career advice and job-related assistance via an interactive bot.
- **Aptitude Portal**: Take company-specific aptitude tests with automatic scoring and difficulty levels.
- **Notifications**: Receive automated email alerts for new jobs matching the user's skillset.

---

## 4. Database Models (Schema)

### **User Table**
- Stores core identity (`username`, `email`, `password`) and profile status.
- Tracks platform engagement (`total_screen_time`, `last_activity`).
- Manages preferences (`notifications_enabled`) and profile assets (`profile_pic`, `resume_filename`).

### **Company Table**
- Stores job roles synchronized from company career boards via API.
- Includes `job_role`, `start_date`, `end_date`, `location`, `job_level`, `experience_required`, and `apply_link`.

### **Resume Data Table**
- Stores structured information extracted from user resumes.
- Fields: `full_name`, `phone`, `skills`, `education`, `experience`, `projects`, `summary`, etc.

### **Notification Table**
- Links users to newly synced jobs.
- Tracks `is_seen` status to avoid duplicate alerts.

### **Aptitude System Tables**
- `aptitude_patterns`: Stores the structure of tests (e.g., questions per section, time limits) for specific companies.
- `aptitude_questions`: A repository of questions categorized by difficulty and section.

### **Resume Templates Table**
- Defines available designs for the Resume Builder, including `demo_data` and `base_layout`.

---

## 5. System Design & Architecture
- **Automatic Sync**: Uses native threading in `app.py` to run background job synchronization every 24 hours without blocking the main web server.
- **Dynamic Dashboard**: Provides immediate access to job listings upon login, with profile enhancement as an optional step.
- **Modular Routes**: Separated into `auth_routes`, `admin_routes`, and `user_routes` for maintainability.

---

## 6. Installation & Setup
1. **Environment**: Install dependencies from `requirements.txt` (including `flask`, `python-dotenv`, `requests`, etc.).
2. **Configuration**: Set up `.env` with `SECRET_KEY`, `MAIL_SERVER`, `MAIL_USERNAME`, and `MAIL_PASSWORD`.
3. **Initialization**: Run `app.py`; the database and default templates will initialize automatically via `database.py`.

---

## 7. Testing & Quality Assurance
The platform undergoes systematic functional, security, and integration testing. A comprehensive testing suite including detailed steps, inputs, pre-conditions, and SQL database assertions has been compiled for QA review:
- Refer to the dedicated [Test Case Specification Document (TEST_CASES.md)](file:///c:/D/CareerConnect/TEST_CASES.md) in the project root directory.
- This includes verification protocols for all security modules (Password boundary checks, Admin 2FA Setup, OAuth linking), automated job API synchronizer, AI resume matching engine, aptitude evaluator, and real-time screen-time tracking analytics.

