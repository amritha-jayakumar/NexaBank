from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, Transaction, LoginAttempt, AuditLog, Beneficiary, SupportTicket, Notification, FixedDeposit
from utils.security import admin_required, super_admin_required, log_admin_action

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
@admin_required
def admin_dashboard():
    users = db.session.execute(db.select(User)).scalars().all()
    txns = db.session.execute(db.select(Transaction).order_by(Transaction.created_at.desc()).limit(20)).scalars().all()
    logs = db.session.execute(db.select(AuditLog).order_by(AuditLog.created_at.desc()).limit(10)).scalars().all()
    login_logs = db.session.execute(db.select(LoginAttempt).order_by(LoginAttempt.created_at.desc()).limit(10)).scalars().all()
    
    stats = {
        'total': db.session.execute(db.select(db.func.count(User.id))).scalar(),
        'active': db.session.execute(db.select(db.func.count(User.id)).filter_by(is_active_acc=True)).scalar(),
        'blocked': db.session.execute(db.select(db.func.count(User.id)).filter_by(is_active_acc=False)).scalar()
    }
    return render_template('admin_dashboard.html', users=users, txns=txns, logs=logs, login_logs=login_logs, stats=stats)

@admin_bp.route('/users')
@login_required
@admin_required
def admin_users():
    search = request.args.get('search', '')
    if search:
        users = db.session.execute(db.select(User).filter(
            (User.full_name.ilike(f'%{search}%')) | 
            (User.email.ilike(f'%{search}%'))
        )).scalars().all()
    else:
        users = db.session.execute(db.select(User)).scalars().all()
    return render_template('admin_users.html', users=users, search=search)

@admin_bp.route('/block/<int:id>', methods=['POST'])
@login_required
@admin_required
def block_user(id):
    user = db.get_or_404(User, id)
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
    user_to_delete = db.get_or_404(User, id)
    
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
    db.session.execute(db.delete(Transaction).filter_by(user_id=uid))
    db.session.execute(db.delete(Beneficiary).filter_by(user_id=uid))
    db.session.execute(db.delete(SupportTicket).filter_by(user_id=uid))
    db.session.execute(db.delete(Notification).filter_by(user_id=uid))
    db.session.execute(db.delete(FixedDeposit).filter_by(user_id=uid))
    db.session.execute(db.delete(LoginAttempt).filter_by(email=email))

    db.session.delete(user_to_delete)
    db.session.commit()
    
    log_admin_action(current_user.id, 'Deleted', f'Deleted user {email}', uid)
    flash(f'User {name} has been deleted successfully.', 'success')
    return redirect(url_for('admin.admin_users'))
