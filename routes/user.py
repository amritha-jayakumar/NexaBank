from flask import Blueprint, render_template, redirect, url_for, flash, request, session, make_response
from flask_login import login_required, logout_user, current_user
from models import db, User, Transaction, Beneficiary, SupportTicket, Notification, FixedDeposit, LoginAttempt
from forms import TransferForm, AddBeneficiaryForm, OpenFDForm, SupportTicketForm, ChangePasswordForm, OTPVerifyForm
from utils.security import user_required
from datetime import datetime
import random
import csv
import io

user_bp = Blueprint('user', __name__)

@user_bp.route('/dashboard')
@login_required
@user_required
def dashboard():
    txns   = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).limit(5).all()
    unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    fds    = FixedDeposit.query.filter_by(user_id=current_user.id, status='active').all()
    from sqlalchemy import func
    debits = db.session.query(Transaction.txn_type, func.sum(Transaction.amount))\
               .filter_by(user_id=current_user.id, direction='debit').group_by(Transaction.txn_type).all()
    spend_data = {t: round(a, 2) for t, a in debits}
    now = datetime.utcnow()
    total_fd = sum([fd.principal for fd in fds])
    return render_template('dashboard.html', user=current_user, txns=txns,
                           unread=unread, fds=fds, total_fd=total_fd, spend_data=spend_data,
                           now=now, now_hour=now.hour)

@user_bp.route('/transactions')
@login_required
@user_required
def transactions():
    page = request.args.get('page', 1, type=int)
    txns = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('transactions.html', user=current_user, txns=txns)

@user_bp.route('/download-statement')
@login_required
@user_required
def download_statement():
    txns = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).all()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Date', 'Reference', 'Description', 'Type', 'Direction', 'Amount', 'Balance After'])
    for t in txns:
        cw.writerow([
            t.created_at.strftime('%Y-%m-%d %H:%M:%S'), t.reference, t.description,
            t.txn_type.upper(), t.direction.upper(), t.amount, t.balance_after
        ])
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=statement_{current_user.account_no}.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@user_bp.route('/transfer', methods=['GET', 'POST'])
@login_required
@user_required
def transfer():
    beneficiaries = Beneficiary.query.filter_by(user_id=current_user.id).all()
    form = TransferForm()
    
    if form.validate_on_submit():
        amt = float(form.amount.data)
        if amt <= 0:
            flash('Invalid amount.', 'danger')
        elif amt > current_user.balance:
            flash('Insufficient balance.', 'danger')
        else:
            session['transfer_pending'] = {
                'beneficiary': form.beneficiary.data,
                'acc_no': form.acc_no.data,
                'amount': amt,
                'remarks': form.remarks.data,
                'txn_type': form.txn_type.data
            }
            otp = str(random.randint(100000, 999999))
            session['transfer_otp'] = otp
            session['transfer_otp_time'] = datetime.utcnow().timestamp()
            
            print(f"\n[DEV MODE] 💸 TRANSFER OTP for {current_user.email}: {otp}\n")
            
            from app import send_otp_email
            send_otp_email(current_user.email, otp, "Fund Transfer Authorization")
            
            flash('OTP sent to your email to authorize the transfer.', 'info')
            return redirect(url_for('user.verify_transfer'))
    return render_template('transfer.html', user=current_user, beneficiaries=beneficiaries, form=form)

@user_bp.route('/verify_transfer', methods=['GET', 'POST'])
@login_required
@user_required
def verify_transfer():
    pending = session.get('transfer_pending')
    if not pending:
        return redirect(url_for('user.transfer'))
        
    otp_time = session.get('transfer_otp_time', 0)
    remaining_time = max(0, int(120 - (datetime.utcnow().timestamp() - otp_time)))
    
    if remaining_time <= 0:
        flash('Transfer OTP expired.', 'danger')
        session.pop('transfer_pending', None)
        session.pop('transfer_otp', None)
        return redirect(url_for('user.transfer'))
        
    form = OTPVerifyForm()
    if form.validate_on_submit():
        if form.otp.data.strip() == session.get('transfer_otp'):
            amount = pending['amount']
            if amount > current_user.balance:
                flash('Insufficient balance.', 'danger')
                session.pop('transfer_pending', None)
                session.pop('transfer_otp', None)
                return redirect(url_for('user.transfer'))
                
            current_user.balance = round(current_user.balance - amount, 2)
            t = Transaction(user_id=current_user.id, txn_type=pending['txn_type'],
                            description=f"{pending['txn_type'].upper()} — {pending['remarks']} to {pending['beneficiary']}",
                            amount=amount, direction='debit', balance_after=current_user.balance,
                            reference=f"NX{random.randint(100000000,999999999)}")
            db.session.add(t)
            db.session.commit()
            
            from app import add_notif
            add_notif(current_user.id, f"Transfer of ₹{amount:,.2f} Sent",
                      f"{pending['txn_type'].upper()} to {pending['beneficiary']} — Ref: {t.reference}", 'info')
            
            session.pop('transfer_pending', None)
            session.pop('transfer_otp', None)
            session.pop('transfer_otp_time', None)
            
            flash(f"₹{amount:,.2f} transferred to {pending['beneficiary']} successfully!", 'success')
            return redirect(url_for('user.transactions'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
    elif request.method == 'POST':
        flash('Validation failed. Make sure you entered exactly 6 digits.', 'danger')
            
    return render_template('otp_verify.html', form=form, title="Verify Transfer", remaining_time=remaining_time, cancel_url=url_for('user.transfer'))

@user_bp.route('/beneficiaries', methods=['GET', 'POST'])
@login_required
@user_required
def beneficiaries():
    bens = Beneficiary.query.filter_by(user_id=current_user.id).all()
    form = AddBeneficiaryForm()
    if form.validate_on_submit():
        b = Beneficiary(user_id=current_user.id, name=form.name.data.strip(),
                        account_no=form.acc_no.data.strip(), ifsc=form.ifsc.data.strip().upper(),
                        bank_name=form.bank_name.data.strip(), nickname=form.nickname.data.strip())
        db.session.add(b)
        db.session.commit()
        
        from app import add_notif
        add_notif(current_user.id, 'Beneficiary Added', f"{b.name} was successfully added to your list.")
        flash('Beneficiary added securely.', 'success')
        return redirect(url_for('user.beneficiaries'))
    return render_template('beneficiaries.html', user=current_user, beneficiaries=bens, form=form)

@user_bp.route('/beneficiary/delete/<int:bid>', methods=['POST'])
@login_required
@user_required
def delete_beneficiary(bid):
    b = Beneficiary.query.filter_by(id=bid, user_id=current_user.id).first_or_404()
    db.session.delete(b)
    db.session.commit()
    flash(f'Beneficiary "{b.name}" removed.', 'success')
    return redirect(url_for('user.beneficiaries'))

@user_bp.route('/fixed-deposits')
@login_required
@user_required
def fixed_deposits():
    fds = FixedDeposit.query.filter_by(user_id=current_user.id).all()
    return render_template('fixed_deposits.html', user=current_user, fds=fds)

@user_bp.route('/open-fd', methods=['GET', 'POST'])
@login_required
@user_required
def open_fd():
    form = OpenFDForm()
    if form.validate_on_submit():
        amt = float(form.principal.data)
        m   = int(form.tenure.data)
        if amt < 5000:
            flash('Minimum FD amount is ₹5,000.', 'danger')
        elif amt > current_user.balance:
            flash('Insufficient savings balance to open this FD.', 'danger')
        else:
            from datetime import timedelta
            current_user.balance = round(current_user.balance - amt, 2)
            rate_map = {3: 6.5, 6: 7.0, 12: 7.5, 24: 8.0, 36: 8.25}
            rate = rate_map.get(m, 7.0)
            mat_amt = round(amt + (amt * rate * (m / 12)) / 100, 2)
            maturity_date = datetime.utcnow() + timedelta(days=m * 30)
            fd_num = f"FD{random.randint(10000000, 99999999)}"
            fd = FixedDeposit(
                user_id=current_user.id,
                principal=amt,
                interest_rate=rate,
                tenure_months=m,
                maturity_amt=mat_amt,
                fd_number=fd_num,
                maturity_date=maturity_date
            )
            db.session.add(fd)
            ref = f"FD{random.randint(10000000,99999999)}"
            t = Transaction(user_id=current_user.id, txn_type='fd',
                            description=f"FD Opened — {m} Months @ {rate}% p.a.",
                            amount=amt, direction='debit', balance_after=current_user.balance,
                            reference=ref)
            db.session.add(t)
            db.session.commit()

            from app import add_notif
            add_notif(current_user.id, 'New Fixed Deposit 🎉', f"FD {fd_num} for ₹{amt:,.2f} @ {rate}% opened.")
            flash('Fixed Deposit opened successfully!', 'success')
            return redirect(url_for('user.fixed_deposits'))
    return render_template('open_fd.html', form=form)

@user_bp.route('/notifications')
@login_required
@user_required
def notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(30).all()
    for n in notifs:
        n.is_read = True
    db.session.commit()
    return render_template('notifications.html', notifications=notifs)

@user_bp.route('/support', methods=['GET', 'POST'])
@login_required
@user_required
def support():
    tickets = SupportTicket.query.filter_by(user_id=current_user.id).order_by(SupportTicket.created_at.desc()).all()
    form = SupportTicketForm()
    if form.validate_on_submit():
        ticket_no = f"TKT{random.randint(1000000, 9999999)}"
        t = SupportTicket(
            user_id=current_user.id,
            subject=form.subject.data.strip(),
            message=form.message.data.strip(),
            category=form.category.data,
            ticket_no=ticket_no
        )
        db.session.add(t)
        db.session.commit()
        flash('Support ticket raised. Our team will contact you securely.', 'success')
        return redirect(url_for('user.support'))
    return render_template('support.html', tickets=tickets, form=form)

@user_bp.route('/security-log')
@login_required
@user_required
def security_log():
    logs = LoginAttempt.query.filter_by(email=current_user.email).order_by(LoginAttempt.created_at.desc()).limit(20).all()
    return render_template('security_log.html', logs=logs)

@user_bp.route('/profile')
@login_required
@user_required
def profile():
    return render_template('profile.html', user=current_user)

@user_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    # Both admins and users can change their password
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
            from app import log_attempt
            log_attempt(current_user.email, False, 'wrong_password_change')
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            from app import add_notif, log_attempt
            add_notif(current_user.id, 'Password Changed 🔒', 'Your account password was successfully updated.')
            log_attempt(current_user.email, True, 'password_changed')
            flash('Password changed successfully. Please log in with your new password.', 'success')
            
            logout_user()
            return redirect(url_for('auth.login'))
    return render_template('change_password.html', form=form)
