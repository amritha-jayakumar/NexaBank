import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app import app, db
from models import User

with app.app_context():
    db.create_all() # To create the new AuditLog table!
    admin = db.session.execute(db.select(User).filter_by(email='aadmin441@gmail.com')).scalar_one_or_none()
    if admin:
        admin.role = 'super_admin'
        db.session.commit()
        print("Admin successfully upgraded to super_admin!")
    else:
        print("Admin user not found.")
