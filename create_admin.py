import sys
from app import app, db
from models import User

def create_admin():
    with app.app_context():
        email = "aadmin441@gmail.com"
        # Check if admin already exists
        if db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none():
            print("Admin user already exists. Email: aadmin441@gmail.com")
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
        print("Admin user created successfully! Email: aadmin441@gmail.com | Password: AdminSecurePass123!")

if __name__ == '__main__':
    create_admin()
