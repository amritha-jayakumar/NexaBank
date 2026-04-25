from flask import (Flask, render_template, redirect, url_for,
                   flash, request, session, make_response)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from flask_wtf.csrf import CSRFProtect
from models import db, User, Transaction, LoginAttempt, Beneficiary, SupportTicket, Notification, FixedDeposit
from forms import SignupForm, LoginForm, TransferForm, AddBeneficiaryForm, OpenFDForm, SupportTicketForm, ChangePasswordForm, OTPVerifyForm
from datetime import datetime, timedelta
from sqlalchemy import func
import random, string, os, io, base64
from functools import wraps
from dotenv import load_dotenv
from flask_mail import Mail, Message

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY']                     = os.environ.get('SECRET_KEY', 'nexabank-ultra-secure-2025-key')
app.config['SQLALCHEMY_DATABASE_URI']        = 'sqlite:///nexabank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED']               = True
app.config['SESSION_COOKIE_HTTPONLY']        = True
app.config['SESSION_COOKIE_SAMESITE']        = 'Lax'
app.config['SESSION_COOKIE_SECURE']          = True
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
login_manager = LoginManager(app)
login_manager.login_view             = 'login'
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
                return redirect(url_for('login'))
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

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access Denied: Administrator privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

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
#  PUBLIC ROUTES
# ══════════════════════════════════════════════════════════════
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

@app.route('/home')
def home():
    return render_template('home.html')

# ── SIGNUP ────────────────────────────────────────────────────
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
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
        seed_user(user)
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html', form=form)

# ── LOGIN ─────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
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

        if user and user.check_password(form.password.data):
            user.failed_attempts = 0
            db.session.commit()
            
            # Simulated OTP Verification
            otp = str(random.randint(100000, 999999))
            session['login_pending_user_id'] = user.id
            session['login_otp'] = otp
            session['login_otp_time'] = datetime.utcnow().timestamp()
            session['login_remember'] = form.remember.data
            
            # Send Email
            send_otp_email(user.email, otp, "Login Authorization")
            
            flash('An OTP has been sent to your registered email.', 'info')
            return redirect(url_for('verify_login'))
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

# ── VERIFY LOGIN OTP ──────────────────────────────────────────
@app.route('/verify_login', methods=['GET', 'POST'])
def verify_login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    user_id = session.get('login_pending_user_id')
    if not user_id:
        flash('Session expired. Please login again.', 'danger')
        return redirect(url_for('login'))
        
    otp_time = session.get('login_otp_time', 0)
    current_time = datetime.utcnow().timestamp()
    remaining_time = max(0, int(120 - (current_time - otp_time)))
    
    if remaining_time <= 0:
        flash('OTP has expired. Please login again.', 'danger')
        session.pop('login_pending_user_id', None)
        session.pop('login_otp', None)
        session.pop('login_otp_time', None)
        session.pop('login_remember', None)
        return redirect(url_for('login'))
        
    form = OTPVerifyForm()
    if form.validate_on_submit():
        if form.otp.data == session.get('login_otp'):
            user = User.query.get(user_id)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            login_user(user, remember=session.get('login_remember', False))
            session.permanent = True  # Enable session timeout
            session['last_active'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            
            # Clear pending OTP from session
            session.pop('login_pending_user_id', None)
            session.pop('login_otp', None)
            session.pop('login_otp_time', None)
            session.pop('login_remember', None)
            
            log_attempt(user.email, True, 'login_success')
            add_notif(user.id, 'New Login Detected 🔐',
                      f'Login from IP {get_ip()} at {datetime.utcnow().strftime("%d %b %Y %I:%M %p")}', 'info')
            flash(f'Welcome back, {user.first_name}! Identity Verified.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
            
    return render_template('otp_verify.html', form=form, title="Verify Login", remaining_time=remaining_time, cancel_url=url_for('login'))

# ── LOGOUT ────────────────────────────────────────────────────
@app.route('/logout')
@login_required
def logout():
    log_attempt(current_user.email, True, 'logout')
    logout_user()
    session.clear()
    flash('You have been logged out securely.', 'info')
    return redirect(url_for('login'))


# ══════════════════════════════════════════════════════════════
#  DASHBOARD & ADMIN
# ══════════════════════════════════════════════════════════════
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    txns = Transaction.query.order_by(Transaction.created_at.desc()).limit(20).all()
    return render_template('admin_dashboard.html', users=users, txns=txns, title="Admin Panel")

@app.route('/dashboard')
@login_required
def dashboard():
    txns   = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).limit(5).all()
    unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    fds    = FixedDeposit.query.filter_by(user_id=current_user.id, status='active').all()
    debits = db.session.query(Transaction.txn_type, func.sum(Transaction.amount))\
               .filter_by(user_id=current_user.id, direction='debit').group_by(Transaction.txn_type).all()
    spend_data = {t: round(a, 2) for t, a in debits}
    now = datetime.utcnow()
    return render_template('dashboard.html', user=current_user, txns=txns,
                           unread=unread, fds=fds, spend_data=spend_data,
                           now=now, now_hour=now.hour)

# ══════════════════════════════════════════════════════════════
#  TRANSACTIONS
# ══════════════════════════════════════════════════════════════
@app.route('/transactions')
@login_required
def transactions():
    page   = request.args.get('page', 1, type=int)
    filter = request.args.get('filter', 'all')
    q = Transaction.query.filter_by(user_id=current_user.id)
    if filter == 'credit': q = q.filter_by(direction='credit')
    elif filter == 'debit': q = q.filter_by(direction='debit')
    txns = q.order_by(Transaction.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('transactions.html', user=current_user, txns=txns, filter=filter)

@app.route('/download-statement')
@login_required
def download_statement():
    txns = Transaction.query.filter_by(user_id=current_user.id)\
             .order_by(Transaction.created_at.desc()).limit(20).all()
    lines = [
        "=" * 65,
        "            NEXABANK — ACCOUNT STATEMENT",
        "=" * 65,
        f"  Account Holder : {current_user.full_name}",
        f"  Account Number : {current_user.masked_account}",
        f"  Generated On   : {datetime.utcnow().strftime('%d %b %Y %I:%M %p')} UTC",
        f"  Current Balance: Rs.{current_user.balance:,.2f}",
        "=" * 65,
        f"{'Date':<14} {'Reference':<14} {'Type':<8} {'Debit':>12} {'Credit':>12} {'Balance':>12}",
        "-" * 65,
    ]
    for t in txns:
        debit  = f"Rs.{t.amount:,.2f}" if t.direction == 'debit'  else ''
        credit = f"Rs.{t.amount:,.2f}" if t.direction == 'credit' else ''
        lines.append(f"{t.created_at.strftime('%d %b %Y'):<14} {t.reference:<14} {t.txn_type.upper():<8} {debit:>12} {credit:>12} Rs.{t.balance_after:>9,.2f}")
    lines += ["-" * 65, "  End of Statement — Last 20 Transactions", "=" * 65]
    resp = make_response('\n'.join(lines))
    resp.headers['Content-Type']        = 'text/plain'
    resp.headers['Content-Disposition'] = 'attachment; filename=NexaBank_Statement.txt'
    return resp

# ══════════════════════════════════════════════════════════════
#  TRANSFER
# ══════════════════════════════════════════════════════════════
@app.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    beneficiaries = Beneficiary.query.filter_by(user_id=current_user.id).all()
    form = TransferForm()
    if form.validate_on_submit():
        try:
            amount      = float(form.amount.data)
            beneficiary = form.beneficiary.data.strip()[:100]
            acc_no      = form.acc_no.data.strip()[:20]
            remarks     = form.remarks.data.strip()[:50]
            txn_type    = form.txn_type.data
            if amount <= 0:
                flash('Enter a valid amount.', 'danger'); return redirect(url_for('transfer'))
            if amount > current_user.balance:
                flash('Insufficient balance.', 'danger'); return redirect(url_for('transfer'))
            
            # Simulated OTP Verification
            otp = str(random.randint(100000, 999999))
            session['transfer_pending'] = {
                'amount': amount,
                'beneficiary': beneficiary,
                'acc_no': acc_no,
                'remarks': remarks,
                'txn_type': txn_type
            }
            session['transfer_otp'] = otp
            session['transfer_otp_time'] = datetime.utcnow().timestamp()
            
            # Send Email
            send_otp_email(current_user.email, otp, "Fund Transfer Authorization")
            
            flash('An OTP has been sent to your registered email.', 'info')
            return redirect(url_for('verify_transfer'))
        except ValueError:
            flash('Invalid amount entered.', 'danger')
            return redirect(url_for('transfer'))
    return render_template('transfer.html', user=current_user, beneficiaries=beneficiaries, form=form)

# ── VERIFY TRANSFER OTP ───────────────────────────────────────
@app.route('/verify_transfer', methods=['GET', 'POST'])
@login_required
def verify_transfer():
    pending = session.get('transfer_pending')
    if not pending:
        flash('No pending transfer found.', 'danger')
        return redirect(url_for('transfer'))
        
    otp_time = session.get('transfer_otp_time', 0)
    current_time = datetime.utcnow().timestamp()
    remaining_time = max(0, int(120 - (current_time - otp_time)))
    
    if remaining_time <= 0:
        flash('OTP has expired. Please initiate transfer again.', 'danger')
        session.pop('transfer_pending', None)
        session.pop('transfer_otp', None)
        session.pop('transfer_otp_time', None)
        return redirect(url_for('transfer'))
        
    form = OTPVerifyForm()
    if form.validate_on_submit():
        if form.otp.data == session.get('transfer_otp'):
            amount = pending['amount']
            if amount > current_user.balance:
                flash('Insufficient balance.', 'danger')
                session.pop('transfer_pending', None)
                session.pop('transfer_otp', None)
                return redirect(url_for('transfer'))
                
            current_user.balance = round(current_user.balance - amount, 2)
            t = Transaction(user_id=current_user.id, txn_type=pending['txn_type'],
                            description=f"{pending['txn_type'].upper()} — {pending['remarks']} to {pending['beneficiary']}",
                            amount=amount, direction='debit', balance_after=current_user.balance,
                            reference=f"NX{random.randint(100000000,999999999)}")
            db.session.add(t)
            db.session.commit()
            
            add_notif(current_user.id, f"Transfer of ₹{amount:,.2f} Sent",
                      f"{pending['txn_type'].upper()} to {pending['beneficiary']} — Ref: {t.reference}", 'info')
            
            session.pop('transfer_pending', None)
            session.pop('transfer_otp', None)
            session.pop('transfer_otp_time', None)
            
            flash(f"₹{amount:,.2f} transferred to {pending['beneficiary']} successfully!", 'success')
            return redirect(url_for('transactions'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
            
    return render_template('otp_verify.html', form=form, title="Verify Transfer", remaining_time=remaining_time, cancel_url=url_for('transfer'))
    return render_template('transfer.html', user=current_user, beneficiaries=beneficiaries, form=form)

# ══════════════════════════════════════════════════════════════
#  BENEFICIARIES
# ══════════════════════════════════════════════════════════════
@app.route('/beneficiaries')
@login_required
def beneficiaries():
    blist = Beneficiary.query.filter_by(user_id=current_user.id).order_by(Beneficiary.created_at.desc()).all()
    return render_template('beneficiaries.html', user=current_user, beneficiaries=blist)

@app.route('/beneficiaries/add', methods=['GET', 'POST'])
@login_required
def add_beneficiary():
    form = AddBeneficiaryForm()
    if form.validate_on_submit():
        name     = form.name.data.strip()[:120]
        acc_no   = form.acc_no.data.strip()[:20]
        ifsc     = form.ifsc.data.strip()[:15].upper()
        bank     = form.bank_name.data.strip()[:60]
        nickname = form.nickname.data.strip()[:50]
        b = Beneficiary(user_id=current_user.id, name=name, account_no=acc_no,
                        ifsc=ifsc, bank_name=bank, nickname=nickname)
        db.session.add(b)
        db.session.commit()
        add_notif(current_user.id, 'Beneficiary Added ✅',
                  f'{name} added to your saved beneficiaries.', 'success')
        flash(f'{name} added to beneficiaries!', 'success')
        return redirect(url_for('beneficiaries'))
    return render_template('add_beneficiary.html', user=current_user, form=form)

@app.route('/beneficiaries/delete/<int:bid>')
@login_required
def delete_beneficiary(bid):
    b = Beneficiary.query.filter_by(id=bid, user_id=current_user.id).first()
    if b:
        name = b.name
        db.session.delete(b)
        db.session.commit()
        flash(f'{name} removed from beneficiaries.', 'info')
    return redirect(url_for('beneficiaries'))

# ══════════════════════════════════════════════════════════════
#  FIXED DEPOSITS
# ══════════════════════════════════════════════════════════════
FD_RATES = {3: 6.5, 6: 7.0, 12: 7.5, 24: 8.0, 36: 8.25}

@app.route('/fixed-deposits')
@login_required
def fixed_deposits():
    fds = FixedDeposit.query.filter_by(user_id=current_user.id).order_by(FixedDeposit.start_date.desc()).all()
    return render_template('fixed_deposits.html', user=current_user, fds=fds, rates=FD_RATES)

@app.route('/fixed-deposits/open', methods=['GET', 'POST'])
@login_required
def open_fd():
    form = OpenFDForm()
    if form.validate_on_submit():
        try:
            principal = float(form.principal.data)
            tenure    = int(form.tenure.data)
            if principal < 1000:
                flash('Minimum FD amount is ₹1,000.', 'danger'); return redirect(url_for('open_fd'))
            if principal > current_user.balance:
                flash('Insufficient balance.', 'danger'); return redirect(url_for('open_fd'))
            rate     = FD_RATES.get(tenure, 7.0)
            maturity = round(principal * (1 + (rate / 100) * (tenure / 12)), 2)
            fd_no    = 'FD' + ''.join(random.choices(string.digits, k=8))
            fd = FixedDeposit(user_id=current_user.id, fd_number=fd_no, principal=principal,
                              interest_rate=rate, tenure_months=tenure, maturity_amt=maturity,
                              maturity_date=datetime.utcnow() + timedelta(days=tenure * 30))
            current_user.balance = round(current_user.balance - principal, 2)
            t = Transaction(user_id=current_user.id, txn_type='fd',
                            description=f'Fixed Deposit Opened — {fd_no}',
                            amount=principal, direction='debit',
                            balance_after=current_user.balance, reference=fd_no)
            db.session.add(fd)
            db.session.add(t)
            db.session.commit()
            add_notif(current_user.id, f'FD Opened — {fd_no}',
                      f'₹{principal:,.2f} for {tenure} months @ {rate}% p.a. Matures: ₹{maturity:,.2f}', 'success')
            flash(f'Fixed Deposit of ₹{principal:,.2f} opened successfully!', 'success')
            return redirect(url_for('fixed_deposits'))
        except ValueError:
            flash('Invalid amount.', 'danger')
            return redirect(url_for('open_fd'))
    return render_template('open_fd.html', user=current_user, rates=FD_RATES, form=form)

# ══════════════════════════════════════════════════════════════
#  NOTIFICATIONS
# ══════════════════════════════════════════════════════════════
@app.route('/notifications')
@login_required
def notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id)\
               .order_by(Notification.created_at.desc()).all()
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return render_template('notifications.html', user=current_user, notifs=notifs)

# ══════════════════════════════════════════════════════════════
#  SUPPORT
# ══════════════════════════════════════════════════════════════
@app.route('/support')
@login_required
def support():
    tickets = SupportTicket.query.filter_by(user_id=current_user.id)\
                .order_by(SupportTicket.created_at.desc()).all()
    return render_template('support.html', user=current_user, tickets=tickets)

@app.route('/support/new', methods=['GET', 'POST'])
@login_required
def new_ticket():
    form = SupportTicketForm()
    if form.validate_on_submit():
        subject  = form.subject.data.strip()[:150]
        message  = form.message.data.strip()
        category = form.category.data
        tno = 'TKT' + ''.join(random.choices(string.digits, k=7))
        t = SupportTicket(user_id=current_user.id, subject=subject,
                          message=message, category=category, ticket_no=tno)
        db.session.add(t)
        db.session.commit()
        add_notif(current_user.id, f'Ticket {tno} Raised',
                  f'Your support request "{subject}" has been received. We will respond within 24 hours.', 'info')
        flash(f'Support ticket {tno} raised successfully!', 'success')
        return redirect(url_for('support'))
    return render_template('new_ticket.html', user=current_user, form=form)

# ══════════════════════════════════════════════════════════════
#  CHANGE PASSWORD
# ══════════════════════════════════════════════════════════════
@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    error = None
    if form.validate_on_submit():
        current_pw = form.current_password.data
        new_pw     = form.new_password.data
        if not current_user.check_password(current_pw):
            error = 'Current password is incorrect.'
        elif current_pw == new_pw:
            error = 'New password must be different from the current one.'
        else:
            current_user.set_password(new_pw)
            db.session.commit()
            add_notif(current_user.id, 'Password Changed 🔐',
                      f'Your password was changed on {datetime.utcnow().strftime("%d %b %Y %I:%M %p")}.', 'warning')
            flash('Password changed successfully!', 'success')
            return redirect(url_for('profile'))
    return render_template('change_password.html', user=current_user, form=form, error=error)

# ══════════════════════════════════════════════════════════════
#  SECURITY LOG & PROFILE
# ══════════════════════════════════════════════════════════════
@app.route('/security-log')
@login_required
def security_log():
    attempts = LoginAttempt.query.filter_by(email=current_user.email)\
                 .order_by(LoginAttempt.created_at.desc()).limit(20).all()
    return render_template('security_log.html', user=current_user, attempts=attempts)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

# ══════════════════════════════════════════════════════════════
#  STARTUP
# ══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("NexaBank ready → http://127.0.0.1:8000")
    app.run(debug=True, port=8000)
