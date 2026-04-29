from flask import (Flask, render_template, redirect, url_for,
                   flash, request, session, make_response)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from flask_wtf.csrf import CSRFProtect
from models import db, User, Transaction, LoginAttempt, Beneficiary, SupportTicket, Notification, FixedDeposit, AuditLog
from forms import SignupForm, LoginForm, TransferForm, AddBeneficiaryForm, OpenFDForm, SupportTicketForm, ChangePasswordForm, OTPVerifyForm
from datetime import datetime, timedelta
from sqlalchemy import func
import random, string, os, io, base64
from functools import wraps
from dotenv import load_dotenv
from flask_mail import Mail, Message
from routes.admin import admin_bp
from routes.auth import auth_bp
from routes.user import user_bp

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY']                     = os.environ.get('SECRET_KEY', 'nexabank-ultra-secure-2025-key')
app.config['SQLALCHEMY_DATABASE_URI']        = 'sqlite:///nexabank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED']               = True
app.config['SESSION_COOKIE_HTTPONLY']        = True
app.config['SESSION_COOKIE_SAMESITE']        = 'Lax'
app.config['SESSION_COOKIE_SECURE']          = False # Set to False for local development
app.config['PERMANENT_SESSION_LIFETIME']     = timedelta(minutes=5)

app.config['MAIL_SERVER']   = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT']     = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS']  = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

mail = Mail(app)

csrf = CSRFProtect(app)

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES    = 15
SESSION_TIMEOUT    = 15

db.init_app(app)

app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)

with app.app_context():
    db.create_all()
    # Temporary upgrade script for the admin
    admin = User.query.filter_by(email='admin@nexabank.com').first()
    if admin and admin.role == 'admin':
        admin.role = 'super_admin'
        db.session.commit()

login_manager = LoginManager(app)
login_manager.login_view             = 'auth.login'
login_manager.login_message          = 'Please log in to access your account.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(uid): return User.query.get(int(uid))

def send_otp_email(recipient_email, otp_code, context="Account Security"):
    try:
        msg = Message(f"NexaBank - {context} OTP", recipients=[recipient_email])
        msg.body = f"Hello,\n\nYour One-Time Password (OTP) for {context} is: {otp_code}\n\nThis code will expire in 2 minutes. Do not share this code with anyone.\n\nSecurely,\nNexaBank Security Team"
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# ── Security Headers ──────────────────────────────────────────
@app.after_request
def sec_headers(r):
    r.headers['X-Content-Type-Options'] = 'nosniff'
    r.headers['X-Frame-Options']        = 'DENY'
    r.headers['X-XSS-Protection']       = '1; mode=block'
    r.headers['Referrer-Policy']        = 'strict-origin-when-cross-origin'
    r.headers['Cache-Control']          = 'no-store, no-cache, must-revalidate'
    return r

# ── Session Timeout ───────────────────────────────────────────
@app.before_request
def check_timeout():
    if current_user.is_authenticated:
        last = session.get('last_active')
        if last:
            elapsed = (datetime.utcnow() - datetime.strptime(last, '%Y-%m-%d %H:%M:%S')).total_seconds()
            if elapsed > SESSION_TIMEOUT * 60:
                logout_user()
                session.clear()
                flash('Session expired due to inactivity. Please log in again.', 'warning')
                return redirect(url_for('auth.login'))
        session['last_active'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        session.permanent = True

# ── Error Handlers ────────────────────────────────────────────
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# ── Helpers ───────────────────────────────────────────────────
def get_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr)


def add_notif(user_id, title, message, ntype='info'):
    n = Notification(user_id=user_id, title=title, message=message, notif_type=ntype)
    db.session.add(n)
    db.session.commit()

def log_attempt(email, success, reason=''):
    try:
        db.session.add(LoginAttempt(email=email, ip_address=get_ip(), success=success, reason=reason))
        db.session.commit()
    except:
        pass

# ── Demo Data ─────────────────────────────────────────────────
DEMO_TXN = [
    ("salary_credit", "Salary Credit — TechCorp Pvt Ltd",  45000.00, "credit"),
    ("upi",           "UPI — Swiggy Food Order",             -452.00, "debit"),
    ("neft",          "NEFT — Rent Payment",               -12000.00, "debit"),
    ("upi",           "UPI — PhonePe to Priya K",           -2000.00, "debit"),
    ("atm",           "ATM Withdrawal — NexaBank ATM",      -5000.00, "debit"),
    ("imps",          "IMPS — Amazon Pay",                  -1299.00, "debit"),
    ("salary_credit", "Interest Credit",                      312.50, "credit"),
    ("upi",           "UPI — Zomato Order",                  -589.00, "debit"),
    ("neft",          "NEFT — Insurance Premium",            -3500.00, "debit"),
    ("imps",          "IMPS — Refund — Flipkart",            1999.00, "credit"),
]

def seed_user(user):
    bal = 50000.00
    for i, (tt, desc, amt, d) in enumerate(DEMO_TXN):
        bal += amt
        t = Transaction(user_id=user.id, txn_type=tt, description=desc,
                        amount=abs(amt), direction=d, balance_after=round(bal, 2),
                        reference=f"NX{random.randint(100000000,999999999)}")
        t.created_at = datetime.utcnow() - timedelta(days=9-i, hours=random.randint(0, 8))
        db.session.add(t)
    user.balance = round(bal, 2)
    b = Beneficiary(user_id=user.id, name='Priya Kumar', account_no='456789012345',
                    ifsc='HDFC0001234', bank_name='HDFC Bank', nickname='Priya')
    db.session.add(b)
    add_notif(user.id, 'Welcome to NexaBank! 🎉',
              f'Hi {user.first_name}, your account is ready. Starting balance: ₹50,000.', 'success')
    add_notif(user.id, 'Security Tip 🔒',
              'Never share your password with anyone — including NexaBank staff.', 'warning')
    db.session.commit()

# ══════════════════════════════════════════════════════════════
#  STARTUP
# ══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("NexaBank ready → http://127.0.0.1:8000")
    app.run(debug=True, port=8000)
