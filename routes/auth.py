from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user
from models import db, User, LoginAttempt
from forms import SignupForm, LoginForm, OTPVerifyForm
from utils.security import get_ip, log_admin_action
from datetime import datetime, timedelta
import random

auth_bp = Blueprint('auth', __name__)

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES    = 15

# Helper functions that need to be here or imported
def log_attempt(email, success, reason=''):
    try:
        db.session.add(LoginAttempt(email=email, ip_address=get_ip(), success=success, reason=reason))
        db.session.commit()
    except:
        pass

# We will need to import send_otp_email and add_notif from app if we don't move them.
# It's better to put them in a utils module, but to avoid circular imports we can import them dynamically
# or move them. Let's assume we move them to utils/helpers.py later, but for now we import from app inside the route
# to avoid circular imports.

@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role in ['admin', 'super_admin']:
            return redirect(url_for('admin.admin_dashboard'))
        return redirect(url_for('user.dashboard'))
    return render_template('home.html')

@auth_bp.route('/home')
def home():
    return render_template('home.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        if current_user.role in ['admin', 'super_admin']:
            return redirect(url_for('admin.admin_dashboard'))
        return redirect(url_for('user.dashboard'))
        
    form = SignupForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash('An account with this email already exists.', 'danger')
            return render_template('signup.html', form=form)
        user = User(
            full_name  = form.full_name.data.strip(),
            email      = form.email.data.lower().strip(),
            phone      = form.phone.data.strip(),
            account_no = User.generate_account_no(),
            balance    = 50000.00,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        from app import seed_user
        seed_user(user)
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('signup.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role in ['admin', 'super_admin']:
            return redirect(url_for('admin.admin_dashboard'))
        return redirect(url_for('user.dashboard'))
        
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user  = User.query.filter_by(email=email).first()

        # Check lockout
        if user and user.is_locked:
            if datetime.utcnow() < (user.locked_until or datetime.utcnow()):
                mins = int(((user.locked_until or datetime.utcnow()) - datetime.utcnow()).total_seconds() // 60) + 1
                flash(f'Account locked due to multiple failed attempts. Try again in {mins} minute(s).', 'danger')
                return render_template('login.html', form=form)
            else:
                user.is_locked = False
                user.failed_attempts = 0
                user.locked_until = None
                db.session.commit()

        if user and not user.is_active_acc:
            flash('Your account has been blocked by an administrator.', 'danger')
            log_attempt(email, False, 'account_blocked')
            return render_template('login.html', form=form)

        if user and user.check_password(form.password.data):
            user.failed_attempts = 0
            db.session.commit()
            
            if user.role in ['admin', 'super_admin']:
                otp = '123456'
                print(f"\n[DEV MODE - ADMIN] 🔐 DUMMY LOGIN OTP for {user.email}: {otp}\n")
            else:
                otp = str(random.randint(100000, 999999))
                print(f"\n[DEV MODE] 🔐 LOGIN OTP for {user.email}: {otp}\n")
                
            session['login_pending_user_id'] = user.id
            session['login_otp'] = otp
            session['login_otp_time'] = datetime.utcnow().timestamp()
            session['login_remember'] = form.remember.data
            
            from app import send_otp_email
            send_otp_email(user.email, otp, "Login Authorization")
            
            flash('An OTP has been sent to your registered email.', 'info')
            return redirect(url_for('auth.verify_login'))
        else:
            if user:
                user.failed_attempts = (user.failed_attempts or 0) + 1
                if user.failed_attempts >= MAX_LOGIN_ATTEMPTS:
                    user.is_locked    = True
                    user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
                    db.session.commit()
                    log_attempt(email, False, 'account_locked_now')
                    flash(f'Account locked for {LOCKOUT_MINUTES} minutes due to too many failed attempts.', 'danger')
                    return render_template('login.html', form=form)
                db.session.commit()
                remaining = MAX_LOGIN_ATTEMPTS - user.failed_attempts
                flash(f'Incorrect password. {remaining} attempt(s) remaining before lockout.', 'danger')
            else:
                flash('Invalid email or password.', 'danger')
            log_attempt(email, False, 'wrong_password')

    return render_template('login.html', form=form)

@auth_bp.route('/verify_login', methods=['GET', 'POST'])
def verify_login():
    if current_user.is_authenticated:
        if current_user.role in ['admin', 'super_admin']:
            return redirect(url_for('admin.admin_dashboard'))
        return redirect(url_for('user.dashboard'))
    
    user_id = session.get('login_pending_user_id')
    if not user_id:
        flash('Session expired. Please login again.', 'danger')
        return redirect(url_for('auth.login'))
        
    otp_time = session.get('login_otp_time', 0)
    current_time = datetime.utcnow().timestamp()
    remaining_time = max(0, int(120 - (current_time - otp_time)))
    
    if remaining_time <= 0:
        flash('OTP has expired. Please login again.', 'danger')
        session.pop('login_pending_user_id', None)
        session.pop('login_otp', None)
        session.pop('login_otp_time', None)
        session.pop('login_remember', None)
        return redirect(url_for('auth.login'))
        
    form = OTPVerifyForm()
    if form.validate_on_submit():
        if form.otp.data.strip() == session.get('login_otp'):
            user = User.query.get(user_id)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            login_user(user, remember=session.get('login_remember', False))
            session.permanent = True
            session['last_active'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            
            session.pop('login_pending_user_id', None)
            session.pop('login_otp', None)
            session.pop('login_otp_time', None)
            session.pop('login_remember', None)
            
            log_attempt(user.email, True, 'login_success')
            
            from app import add_notif
            add_notif(user.id, 'New Login Detected 🔐',
                      f'Login from IP {get_ip()} at {datetime.utcnow().strftime("%d %b %Y %I:%M %p")}', 'info')
                      
            # ADD ADMIN LOGIN AUDIT LOG HERE
            if user.role in ['admin', 'super_admin']:
                log_admin_action(user.id, 'Login', 'Admin logged into the system')
                
            flash(f'Welcome back, {user.first_name}! Identity Verified.', 'success')
            if user.role in ['admin', 'super_admin']:
                return redirect(url_for('admin.admin_dashboard'))
            return redirect(url_for('user.dashboard'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
    elif request.method == 'POST':
        flash('Validation failed. Make sure you entered exactly 6 digits.', 'danger')
            
    return render_template('otp_verify.html', form=form, title="Verify Login", remaining_time=remaining_time, cancel_url=url_for('auth.login'))

@auth_bp.route('/logout')
def logout():
    if current_user.is_authenticated:
        log_attempt(current_user.email, True, 'logout')
        logout_user()
    session.clear()
    flash('You have been logged out securely.', 'info')
    return redirect(url_for('auth.login'))
