<div align="center">
  <img src="https://img.shields.io/badge/Status-Completed-success?style=for-the-badge&logo=git&logoColor=white" alt="Completed" />
</div>

<br>

<div align="center">
  <h1>NexaBank — Identity Security Framework</h1>
  <p><strong>PRJN26-158 | Cyber Security, Ethical Hacking & Digital Forensics</strong></p>
  <p>Status: Completed</p>
  <p>A successfully developed and implemented secure, full-featured banking system designed to demonstrate robust identity and transaction security.</p>
</div>

<div align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" />
  <img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML5" />
  <img src="https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white" alt="CSS3" />
  <br>
  <img src="https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge" alt="License: MIT" />
</div>

---

## Project Overview

NexaBank is a fully developed and functional banking web application. The primary purpose of this project is to implement a secure banking system with a strong emphasis on identity security. It serves as a comprehensive framework demonstrating secure authentication, authorization, and safe financial transaction processing.

---

## Features Implemented

- Two-Factor Authentication (Password + OTP)
- Secure password hashing (bcrypt/scrypt via Werkzeug)
- CSRF protection
- Account lockout for brute-force prevention
- Audit logging (IP, timestamp, login status)
- Banking features (fund transfer, beneficiary management, fixed deposits)

---

## Technologies Used

- Flask
- SQLite
- HTML/CSS
- Python

---

## Security Features

1. **Password Hashing**: Passwords are mathematically transformed and stored securely, ensuring they cannot be easily retrieved if the database is compromised.
2. **CSRF Protection**: Prevents malicious sites from executing unwanted actions on behalf of the authenticated user.
3. **Route Protection**: Ensures that only authenticated users can access sensitive pages, strictly enforcing access control.
4. **Session Management**: User sessions are securely managed and cryptographically signed to prevent tampering.
5. **Input Validation**: All user inputs are rigorously checked on the server side to prevent injection attacks and ensure data integrity.
6. **Account Lockout**: The system temporarily disables accounts after multiple failed login attempts to thwart brute-force password guessing attacks.

---

## Project Completion Note

This project has been successfully completed as part of an academic submission. It fulfills all specified requirements for demonstrating a functional and secure identity management framework within a simulated banking environment.

---

## Future Enhancements

While the core objectives have been met, future iterations of this project could explore the following areas:

- **Deployment**: Transitioning the application from a local development environment to a secure cloud hosting platform (e.g., AWS, Heroku, or PythonAnywhere).
- **Advanced Monitoring**: Integrating comprehensive application performance monitoring and intrusion detection systems to proactively identify and respond to threats.
- **Scalability Improvements**: Migrating from SQLite to a more robust, scalable database system like PostgreSQL or MySQL to handle increased data volume and concurrent users.

---

## Complete File Structure

```text
NexaBank/
│
├── app.py                   ← Flask app + all routes (main file)
├── models.py                ← User & Transaction database models
├── forms.py                 ← Signup & Login form validation
├── requirements.txt         ← All Python packages needed
│
├── templates/               ← HTML pages (Jinja2 templates)
│   ├── base.html            ← Master layout (navbar, flash msgs, footer)
│   ├── home.html            ← Public landing page (hero, features)
│   ├── login.html           ← NetBanking login page
│   ├── signup.html          ← Account opening / registration page
│   ├── dashboard.html       ← Main dashboard (balance, quick actions)
│   ├── transactions.html    ← Full transaction history table
│   ├── transfer.html        ← NEFT / IMPS / UPI fund transfer
│   └── profile.html         ← User profile & account details
│
├── static/
│   ├── css/
│   │   └── style.css        ← Complete banking CSS (900+ lines)
│   └── js/
│       └── main.js          ← Password toggle, strength, transfer preview
│
└── instance/
    └── nexabank.db          ← SQLite database (auto-created on first run)
```

---

## SETUP — Step by Step (VS Code)

### Step 1 — Open in VS Code
Open your `NexaBank` folder in Visual Studio Code.

### Step 2 — Open Terminal
Press `` Ctrl + ` `` or go to `Terminal → New Terminal`.

### Step 3 — Create Virtual Environment
```bash
python -m venv venv
```

### Step 4 — Activate Virtual Environment
**Windows:**
```bash
venv\Scripts\activate
```
**Mac / Linux:**
```bash
source venv/bin/activate
```
*(You should see `(venv)` in your terminal prompt.)*

### Step 5 — Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 6 — Run the App
```bash
python app.py
```
You will see output similar to:
```
  NexaBank database ready.
  Open http://127.0.0.1:5000
 * Running on http://127.0.0.1:5000
```

### Step 7 — View in Browser
Open `http://127.0.0.1:5000` in any web browser.

---

## Pages & Routes

| URL              | Page              | Access      |
|------------------|-------------------|-------------|
| `/`              | Landing Page      | Public      |
| `/signup`        | Open Account      | Public      |
| `/login`         | NetBanking Login  | Public      |
| `/dashboard`     | Account Dashboard | Login req   |
| `/transactions`  | Statement History | Login req   |
| `/transfer`      | Fund Transfer     | Login req   |
| `/profile`       | My Profile        | Login req   |
| `/logout`        | Logout            | Login req   |

---

## Cybersecurity Concepts in Code

| Concept               | Where                                  |
|-----------------------|----------------------------------------|
| Authentication        | `/login` — email+password verification |
| Password Hashing      | `models.py → set_password()` pbkdf2    |
| Hash Verification     | `models.py → check_password()`         |
| Session Management    | `login_user()` / `logout_user()`       |
| Authorization Guard   | `@login_required` on all private pages |
| CSRF Protection       | `form.hidden_tag()` in every form      |
| Server-side Validation| `forms.py` — WTForms validators        |
| SQLite ORM Storage    | SQLAlchemy models                      |
| Transaction Audit Log | `Transaction` model with reference no. |

---

## Troubleshooting

| Problem                    | Solution                                      |
|----------------------------|-----------------------------------------------|
| `ModuleNotFoundError`      | Run `pip install -r requirements.txt`         |
| `OperationalError`         | Delete `instance/nexabank.db`, restart app    |
| Port 5000 already in use   | Add `app.run(port=5001)` in `app.py`          |
| Form won't submit (CSRF)   | Make sure `form.hidden_tag()` is in template  |
| White page / no styles     | Check `static/css/style.css` path is correct  |

<br>

<div align="center">
  <p>Crafted with Security and for Learning.</p>
</div>
