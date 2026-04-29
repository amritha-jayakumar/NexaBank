import sys
from app import app, db
from models import User

def create_admin():
    with app.app_context():
        email = "admin@nexabank.com"
        # Check if admin already exists
        if User.query.filter_by(email=email).first():
            print("Admin user already exists. Email: admin@nexabank.com")
            return

        admin_user = User(
            full_name="System Administrator",
            email=email,
            phone="0000000000",
            account_no=User.generate_account_no(),
            role="admin",
            balance=0.0
        )
        # Use the existing set_password method
        admin_user.set_password("AdminSecurePass123!")
        
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created successfully! Email: admin@nexabank.com | Password: AdminSecurePass123!")

if __name__ == '__main__':
    create_admin()
