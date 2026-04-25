# 🏦 NexaBank — Identity Security Framework
### PRJN26-158 | Cyber Security, Ethical Hacking & Digital Forensics

A full banking website built with Python, Flask-Login & SQLite.
Inspired by HDFC Bank / Federal Bank NetBanking portals.

---

## 📁 Complete File Structure

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

## 🚀 SETUP — Step by Step (VS Code)

### Step 1 — Open in VS Code
```
File → Open Folder → select the NexaBank folder
```

### Step 2 — Open Terminal in VS Code
```
Terminal → New Terminal   (or press Ctrl + ` )
```

### Step 3 — Create virtual environment
```bash
python -m venv venv
```

### Step 4 — Activate virtual environment
```bash
# Windows:
venv\Scripts\activate

# Mac / Linux:
source venv/bin/activate
```
You should see `(venv)` in your terminal prompt.

### Step 5 — Install all packages
```bash
pip install -r requirements.txt
```

### Step 6 — Run the app
```bash
python app.py
```

You will see:
```
✅  NexaBank database ready.
🌐  Open http://127.0.0.1:5000
 * Running on http://127.0.0.1:5000
```

### Step 7 — Open in browser
```
http://127.0.0.1:5000
```

---

## 🌐 Pages & Routes

| URL              | Page              | Access      |
|------------------|-------------------|-------------|
| /                | Landing Page      | Public      |
| /signup          | Open Account      | Public      |
| /login           | NetBanking Login  | Public      |
| /dashboard       | Account Dashboard | 🔒 Login req |
| /transactions    | Statement History | 🔒 Login req |
| /transfer        | Fund Transfer     | 🔒 Login req |
| /profile         | My Profile        | 🔒 Login req |
| /logout          | Logout            | 🔒 Login req |

---

## 🎓 Cybersecurity Concepts in Code

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

## 🔒 Security Features

1. **Password Hashing** — Stored as `pbkdf2:sha256` hash. Completely irrecoverable.
2. **CSRF Tokens** — Every form has a hidden CSRF token via Flask-WTF.
3. **Route Protection** — `@login_required` redirects unauthorized users to login.
4. **Session Cookie** — Signed with SECRET_KEY; tampering is automatically detected.
5. **Input Validation** — All inputs validated server-side before touching the database.
6. **Email Deduplication** — Duplicate accounts blocked at registration.

---

## 🛠 Troubleshooting

| Problem                    | Solution                                      |
|----------------------------|-----------------------------------------------|
| `ModuleNotFoundError`      | Run `pip install -r requirements.txt`         |
| `OperationalError`         | Delete `instance/nexabank.db`, restart app    |
| Port 5000 already in use   | Add `app.run(port=5001)` in app.py            |
| Form won't submit (CSRF)   | Make sure `form.hidden_tag()` is in template  |
| White page / no styles     | Check `static/css/style.css` path is correct  |
