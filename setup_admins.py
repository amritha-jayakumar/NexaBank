from app import app, db
from models import User

def setup_both_admins():
    with app.app_context():
        emails = ["admin@nexabank.com", "aadmin441@gmail.com"]
        for email in emails:
            admin = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
            if not admin:
                print(f"Creating admin account for {email}...")
                admin = User(
                    full_name="System Administrator",
                    email=email,
                    phone="0000000000",
                    account_no=User.generate_account_no(),
                    role="super_admin",
                    balance=0.0
                )
                db.session.add(admin)
            else:
                print(f"Found admin account for {email}. Resetting role and password...")
                admin.role = "super_admin"
                admin.is_active_acc = True
                admin.is_locked = False
                admin.failed_attempts = 0
            
            admin.set_password("AdminSecurePass123!")
        
        db.session.commit()
        print("Success! Both admin accounts are now configured as super admins.")

if __name__ == '__main__':
    setup_both_admins()
