# Software Requirements Specification (SRS)
## Project Name: CareerConnect - Intelligent Job & Resume Portal

---

### 1. Introduction
#### 1.1 Purpose
The purpose of this document is to define the functional and non-functional requirements for the **CareerConnect** platform. This application aims to streamline the job application process by aggregating relevant jobs from major tech companies and matching them with user resume profiles.

#### 1.2 Scope
CareerConnect is a Flask-based web application that provides:
- A unified multi-role authentication system (Admin & User).
- Automated job fetching from external APIs (Adzuna).
- AI-driven resume data extraction and profile completion.
- Interactive dashboards for both applicants and recruiters.

---

### 2. Overall Description
#### 2.1 Product Perspective
The system acts as a centralized hub for job seekers and administrators. It connects to the **Adzuna API** for real-time market data and uses local processing for resume analysis and company management.

#### 2.2 User Classes
1.  **Job Seeker (User)**:
    - Creates a profile by uploading a resume.
    - Views job listings matching their skills and experience.
    - Tracks applied jobs and dashboard statistics.
2.  **Administrator**:
    - Manages the list of monitored companies.
    - Configures job titles and roles to be scraped.
    - Monitors user activity and resume data.

---

### 3. System Features

#### 3.1 Multi-Role Authentication
- **F-01**: The system shall provide a single login/signup page.
- **F-02**: The system shall redirect users to `/user/dashboard` and admins to `/admin/dashboard` based on their role stored in the database.

#### 3.2 Automated Job Aggregation
- **F-03**: The system shall fetch job listings from the Adzuna API based on a predefined list of companies (e.g., Google, Amazon, TCS).
- **F-04**: The system shall filter jobs based on specific roles (e.g., Python Developer, Software Engineer) and posting date (default: last 30 days).
- **F-05**: The system shall prevent duplicate job entries by checking unique redirect URLs.

#### 3.3 Resume Extraction & Profile Management
- **F-06**: Users shall be able to upload resumes in PDF format.
- **F-07**: The system shall extract name, contact details, skills, experience, and education from the resume.
- **F-08**: Users shall be able to edit their extracted profile information via a completion form.

#### 3.4 Admin Company Management
- **F-09**: Admins shall be able to add new companies to the monitoring list.
- **F-10**: Admins shall be able to set official page links and specific job roles for each company.

---

### 4. External Interface Requirements
#### 4.1 User Interface
- Modern, responsive design using **Vanilla CSS**.
- Dashboard widgets for data visualization (Total Jobs, Applied Jobs, Profile Completion).
- Interactive navigation bar with role-specific links.

#### 4.2 API Interfaces
- **Adzuna API**: Used for fetching real-time job data via `APP_ID` and `APP_KEY`.
- **SMTP (Gmail)**: Used for sending automated email notifications to users.

---

### 5. Non-Functional Requirements
#### 5.1 Security
- All user data must be stored in a secured SQLite database.
- Admin routes must be protected using session-based authentication.

#### 5.2 Performance
- Job fetching logic (Job Service) should execute efficiently without crashing the main application thread.
- Resume parsing should provide immediate feedback to the user.

---

### 6. Database Schema
- **user**: Stores credentials, emails, and roles.
- **resume_data**: Stores parsed information (Skills, Phone, Summary, etc.).
- **company**: Stores monitored company names, links, and job roles.

---

### 7. Appendix
- **Frontend**: HTML5, CSS3, Javascript.
- **Backend**: Python, Flask, SQLite.
- **Services**: Adzuna API, Email SMTP Service.
