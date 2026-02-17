# Multi-Role Login System

This application provides a single Sign-In/Sign-Up page for both Admins and Users.

## Features
- **Single Page Authentication**: Toggle between Login and Sign Up.
- **Role-Based Access**: 
  - **Admins** are routed to the Admin Dashboard (`templates/admin/`).
  - **Users** are routed to the User Dashboard (`templates/user/`).
- **Database**: All data is stored in a SQLite `user` table with a `role` column.
- **Modern Design**: Responsive and animated UI.

## How to Run
1. Install Flask:
   ```bash
   pip install flask
   ```
2. Run the application:
   ```bash
   python app.py
   ```
3. Open your browser at `http://127.0.0.1:5000`.

## Directory Structure
- `app.py`: Main application logic.
- `templates/`: HTML files.
  - `login.html`: Unified login/signup page.
  - `admin/`: Admin-specific pages ("directory for admin user").
  - `user/`: User-specific pages.
- `static/`: CSS and assets.
