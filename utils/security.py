from functools import wraps
from flask import flash, redirect, url_for, request
from flask_login import current_user
from models import db, AuditLog
from datetime import datetime

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'super_admin']:
            flash('Access Denied: Administrator privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'super_admin':
            flash('Access Denied: Super Administrator privileges required.', 'danger')
            return redirect(url_for('admin.admin_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role in ['admin', 'super_admin']:
            flash('Administrators cannot access customer banking features.', 'danger')
            return redirect(url_for('admin.admin_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def get_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr)

def log_admin_action(admin_id, action, details='', target_id=None):
    try:
        log = AuditLog(
            admin_id=admin_id,
            target_id=target_id,
            action=action,
            details=details,
            ip_address=get_ip()
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Audit log failed: {e}")
