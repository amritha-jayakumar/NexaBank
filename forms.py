"""
forms.py — Flask-WTF forms for NexaBank
"""

from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, BooleanField,
                     SubmitField, TelField)
from wtforms.validators import (DataRequired, Email, Length,
                                EqualTo, Regexp, ValidationError)
import re


class SignupForm(FlaskForm):
    """New account registration form."""

    full_name = StringField(
        'Full Name',
        validators=[
            DataRequired('Full name is required.'),
            Length(min=3, max=120, message='Name must be 3–120 characters.'),
            Regexp(r'^[A-Za-z ]+$', message='Name can only contain letters and spaces.')
        ]
    )
    email = StringField(
        'Email Address',
        validators=[
            DataRequired('Email is required.'),
            Email('Enter a valid email address.'),
            Length(max=150)
        ]
    )
    phone = StringField(
        'Mobile Number',
        validators=[
            DataRequired('Mobile number is required.'),
            Regexp(r'^[6-9]\d{9}$', message='Enter a valid 10-digit Indian mobile number.')
        ]
    )
    password = PasswordField(
        'Create Password',
        validators=[
            DataRequired('Password is required.'),
            Length(min=8, message='Password must be at least 8 characters.'),
            Regexp(
                r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$',
                message='Password must have at least 1 uppercase, 1 lowercase, 1 number, and 1 special character.'
            )
        ]
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired('Please confirm your password.'),
            EqualTo('password', message='Passwords must match.')
        ]
    )
    submit = SubmitField('Open Account')


class LoginForm(FlaskForm):
    """Login form."""

    email = StringField(
        'Email / User ID',
        validators=[
            DataRequired('Email is required.'),
            Email('Enter a valid email address.')
        ]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired('Password is required.')]
    )
    remember = BooleanField('Keep me logged in')
    submit   = SubmitField('Login to NetBanking')

class TransferForm(FlaskForm):
    beneficiary = StringField('Beneficiary Name', validators=[DataRequired(), Length(max=100)])
    acc_no = StringField('Account Number', validators=[DataRequired(), Length(max=20)])
    amount = StringField('Amount (₹)', validators=[DataRequired(), Regexp(r'^\d+(\.\d{1,2})?$', message='Enter a valid positive amount')])
    remarks = StringField('Remarks', validators=[Length(max=50)])
    txn_type = StringField('Transfer Type', validators=[DataRequired()])
    submit = SubmitField('Transfer Funds')

class AddBeneficiaryForm(FlaskForm):
    name = StringField('Beneficiary Name', validators=[DataRequired(), Length(max=120)])
    acc_no = StringField('Account Number', validators=[DataRequired(), Length(max=20)])
    ifsc = StringField('IFSC Code', validators=[DataRequired(), Length(max=15)])
    bank_name = StringField('Bank Name', validators=[DataRequired(), Length(max=60)])
    nickname = StringField('Nickname', validators=[Length(max=50)])
    submit = SubmitField('Add Beneficiary')

class OpenFDForm(FlaskForm):
    principal = StringField('Deposit Amount (₹)', validators=[DataRequired(), Regexp(r'^\d+(\.\d{1,2})?$', message='Enter a valid positive amount')])
    tenure = StringField('Tenure (Months)', validators=[DataRequired()])
    submit = SubmitField('Open Fixed Deposit')

class SupportTicketForm(FlaskForm):
    subject = StringField('Subject', validators=[DataRequired(), Length(max=150)])
    message = StringField('Message', validators=[DataRequired()])
    category = StringField('Category', validators=[DataRequired()])
    submit = SubmitField('Submit Ticket')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters.'),
        Regexp(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$', message='Password must have at least 1 uppercase, 1 lowercase, 1 number, and 1 special character.')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match.')
    ])
    submit = SubmitField('Change Password')

class OTPVerifyForm(FlaskForm):
    otp = StringField('Enter 6-Digit OTP', validators=[
        DataRequired(),
        Regexp(r'^\d{6}$', message='OTP must be exactly 6 digits.')
    ])
    submit = SubmitField('Verify')
