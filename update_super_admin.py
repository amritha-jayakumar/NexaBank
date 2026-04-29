import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app import app, db
from models import User

with app.app_context():
    db.create_all() # To create the new AuditLog table!
    admin = User.query.filter_by(email='admin@nexabank.com').first()
    if admin:
        admin.role = 'super_admin'
        db.session.commit()
        print("Admin successfully upgraded to super_admin!")
    else:
        print("Admin user not found.")
