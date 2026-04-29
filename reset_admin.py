from app import app, db
from models import User

with app.app_context():
    admin = User.query.filter_by(email="admin@nexabank.com").first()
    if not admin:
        print("Admin user not found. Creating one...")
        admin = User(
            full_name="System Administrator",
            email="admin@nexabank.com",
            phone="0000000000",
            account_no=User.generate_account_no(),
            role="super_admin",
            balance=0.0
        )
        db.session.add(admin)
    else:
        print("Admin user found. Resetting password and ensuring super_admin role...")
        admin.role = "super_admin"
        admin.is_active_acc = True
        admin.is_locked = False
        admin.failed_attempts = 0
    
    admin.set_password("AdminSecurePass123!")
    db.session.commit()
    print("Success! You can now log in with email: admin@nexabank.com and password: AdminSecurePass123!")
