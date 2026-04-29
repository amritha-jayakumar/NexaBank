from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, Transaction, LoginAttempt, AuditLog, Beneficiary, SupportTicket, Notification, FixedDeposit
from utils.security import admin_required, super_admin_required, log_admin_action

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    txns = Transaction.query.order_by(Transaction.created_at.desc()).limit(20).all()
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()
    login_logs = LoginAttempt.query.order_by(LoginAttempt.created_at.desc()).limit(10).all()
    
    stats = {
        'total': User.query.count(),
        'active': User.query.filter_by(is_active_acc=True).count(),
        'blocked': User.query.filter_by(is_active_acc=False).count()
    }
    return render_template('admin_dashboard.html', users=users, txns=txns, logs=logs, login_logs=login_logs, stats=stats)

@admin_bp.route('/users')
@login_required
@admin_required
def admin_users():
    search = request.args.get('search', '')
    if search:
        users = User.query.filter(
            (User.full_name.ilike(f'%{search}%')) | 
            (User.email.ilike(f'%{search}%'))
        ).all()
    else:
        users = User.query.all()
    return render_template('admin_users.html', users=users, search=search)

@admin_bp.route('/block/<int:id>', methods=['POST'])
@login_required
@admin_required
def block_user(id):
    user = User.query.get_or_404(id)
    if user.role in ['admin', 'super_admin'] and current_user.role != 'super_admin':
        flash('Cannot modify administrator accounts without super admin access.', 'danger')
        return redirect(url_for('admin.admin_users'))
        
    if user.id == current_user.id:
        flash('You cannot block yourself.', 'danger')
        return redirect(url_for('admin.admin_users'))
        
    user.is_active_acc = not user.is_active_acc
    action_text = 'Unblocked' if user.is_active_acc else 'Blocked'
    db.session.commit()
    
    log_admin_action(current_user.id, action_text, f'{action_text} user {user.email}', user.id)
    flash(f'User {user.full_name} has been {action_text.lower()}.', 'success')
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    user_to_delete = User.query.get_or_404(id)
    
    if user_to_delete.role in ['admin', 'super_admin'] and current_user.role != 'super_admin':
        flash('Cannot delete an administrator account without super admin privileges.', 'danger')
        return redirect(url_for('admin.admin_users'))
        
    if user_to_delete.id == current_user.id:
        flash('You cannot delete yourself.', 'danger')
        return redirect(url_for('admin.admin_users'))
    
    name = user_to_delete.full_name
    email = user_to_delete.email
    uid = user_to_delete.id

    # Delete ALL related records first to avoid FK constraint errors
    Transaction.query.filter_by(user_id=uid).delete()
    Beneficiary.query.filter_by(user_id=uid).delete()
    SupportTicket.query.filter_by(user_id=uid).delete()
    Notification.query.filter_by(user_id=uid).delete()
    FixedDeposit.query.filter_by(user_id=uid).delete()
    LoginAttempt.query.filter_by(email=email).delete()

    db.session.delete(user_to_delete)
    db.session.commit()
    
    log_admin_action(current_user.id, 'Deleted', f'Deleted user {email}', uid)
    flash(f'User {name} has been deleted successfully.', 'success')
    return redirect(url_for('admin.admin_users'))
