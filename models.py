"""
models.py — NexaBank Database Models
New: Beneficiary, SupportTicket, Notification, FixedDeposit
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random, string, bcrypt

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id              = db.Column(db.Integer,   primary_key=True)
    full_name       = db.Column(db.String(120), nullable=False)
    email           = db.Column(db.String(150), unique=True, nullable=False)
    phone           = db.Column(db.String(15),  nullable=False)
    account_no      = db.Column(db.String(20),  unique=True, nullable=False)
    password_hash   = db.Column(db.String(256), nullable=False)
    balance         = db.Column(db.Float,   default=0.0)
    account_type    = db.Column(db.String(30),  default='Savings Account')
    ifsc_code       = db.Column(db.String(15),  default='NEXA0001234')
    branch          = db.Column(db.String(60),  default='NexaBank Main Branch')
    role            = db.Column(db.String(20),  default='customer')
    failed_attempts = db.Column(db.Integer,  default=0)
    is_locked       = db.Column(db.Boolean,  default=False)
    locked_until    = db.Column(db.DateTime, nullable=True)
    is_active_acc   = db.Column(db.Boolean,  default=True)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    last_login      = db.Column(db.DateTime, nullable=True)

    transactions  = db.relationship('Transaction',  backref='user', lazy=True, order_by='Transaction.created_at.desc()')
    beneficiaries = db.relationship('Beneficiary',  backref='user', lazy=True)
    tickets       = db.relationship('SupportTicket',backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    fds           = db.relationship('FixedDeposit', backref='user', lazy=True)

    def set_password(self, plain):
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(plain.encode('utf-8'), salt).decode('utf-8')
    def check_password(self, plain):
        if self.password_hash.startswith('scrypt:'):
            return check_password_hash(self.password_hash, plain)
        try:
            return bcrypt.checkpw(plain.encode('utf-8'), self.password_hash.encode('utf-8'))
        except ValueError:
            return False
    @staticmethod
    def generate_account_no():
        return ''.join(random.choices(string.digits, k=12))
    @property
    def masked_account(self):
        return 'x'*8 + self.account_no[-4:]
    @property
    def first_name(self):
        return self.full_name.split()[0]


class Transaction(db.Model):
    __tablename__ = 'transactions'
    id            = db.Column(db.Integer,     primary_key=True)
    user_id       = db.Column(db.Integer,     db.ForeignKey('users.id'), nullable=False)
    txn_type      = db.Column(db.String(30),  nullable=False)
    description   = db.Column(db.String(200), nullable=False)
    amount        = db.Column(db.Float,       nullable=False)
    direction     = db.Column(db.String(6),   nullable=False)
    balance_after = db.Column(db.Float,       nullable=False)
    reference     = db.Column(db.String(30),  nullable=False)
    created_at    = db.Column(db.DateTime,    default=datetime.utcnow)
    @property
    def txn_icon(self):
        return {'salary_credit':'💰','neft':'🏦','upi':'📱','imps':'⚡','atm':'🏧','fd':'🏛️'}.get(self.txn_type,'💳')


class Beneficiary(db.Model):
    __tablename__ = 'beneficiaries'
    id          = db.Column(db.Integer,    primary_key=True)
    user_id     = db.Column(db.Integer,    db.ForeignKey('users.id'), nullable=False)
    name        = db.Column(db.String(120),nullable=False)
    account_no  = db.Column(db.String(20), nullable=False)
    ifsc        = db.Column(db.String(15), nullable=False)
    bank_name   = db.Column(db.String(60), nullable=False)
    nickname    = db.Column(db.String(50), default='')
    created_at  = db.Column(db.DateTime,  default=datetime.utcnow)


class SupportTicket(db.Model):
    __tablename__ = 'support_tickets'
    id          = db.Column(db.Integer,    primary_key=True)
    user_id     = db.Column(db.Integer,    db.ForeignKey('users.id'), nullable=False)
    subject     = db.Column(db.String(150),nullable=False)
    message     = db.Column(db.Text,       nullable=False)
    category    = db.Column(db.String(50), default='general')
    status      = db.Column(db.String(20), default='open')
    ticket_no   = db.Column(db.String(15), nullable=False)
    created_at  = db.Column(db.DateTime,  default=datetime.utcnow)
    @property
    def status_color(self):
        return {'open':'blue','in_progress':'amber','resolved':'green','closed':'gray'}.get(self.status,'blue')


class Notification(db.Model):
    __tablename__ = 'notifications'
    id          = db.Column(db.Integer,    primary_key=True)
    user_id     = db.Column(db.Integer,    db.ForeignKey('users.id'), nullable=False)
    title       = db.Column(db.String(150),nullable=False)
    message     = db.Column(db.Text,       nullable=False)
    notif_type  = db.Column(db.String(30), default='info')
    is_read     = db.Column(db.Boolean,    default=False)
    created_at  = db.Column(db.DateTime,  default=datetime.utcnow)


class FixedDeposit(db.Model):
    __tablename__ = 'fixed_deposits'
    id            = db.Column(db.Integer,  primary_key=True)
    user_id       = db.Column(db.Integer,  db.ForeignKey('users.id'), nullable=False)
    fd_number     = db.Column(db.String(15),nullable=False)
    principal     = db.Column(db.Float,    nullable=False)
    interest_rate = db.Column(db.Float,    nullable=False)
    tenure_months = db.Column(db.Integer,  nullable=False)
    maturity_amt  = db.Column(db.Float,    nullable=False)
    start_date    = db.Column(db.DateTime, default=datetime.utcnow)
    maturity_date = db.Column(db.DateTime, nullable=False)
    status        = db.Column(db.String(20),default='active')
    @property
    def days_remaining(self):
        delta = self.maturity_date - datetime.utcnow()
        return max(0, delta.days)


class LoginAttempt(db.Model):
    __tablename__ = 'login_attempts'
    id         = db.Column(db.Integer,    primary_key=True)
    email      = db.Column(db.String(150),nullable=False)
    ip_address = db.Column(db.String(50), nullable=False)
    success    = db.Column(db.Boolean,    nullable=False)
    reason     = db.Column(db.String(50), default='')
    created_at = db.Column(db.DateTime,  default=datetime.utcnow)
    @property
    def status_label(self):
        return {'login_success':'✅ Login Success','password_ok_awaiting_otp':'🔐 Password OK',
                'wrong_password':'❌ Wrong Password','wrong_otp':'❌ Wrong OTP',
                'account_locked':'🔒 Account Locked','account_locked_now':'🔒 Account Locked',
                'otp_brute_force':'⚠️ OTP Brute Force','user_not_found':'❓ User Not Found',
                'logout':'👋 Logged Out'}.get(self.reason, self.reason)
