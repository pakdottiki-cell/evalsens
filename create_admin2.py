from app import app, db, bcrypt
from models.user import User
import sys

print("=== Creating Backup Admin Account (admin2) ===")

with app.app_context():
    # Check if admin2 exists
    admin2 = User.query.filter_by(username='admin2').first()
    if admin2:
        print("admin2 already exists. Updating password...")
        admin2.set_password('admin123')
        admin2.role = 'admin'
        admin2.is_active = True
        print("  - Updated.")
    else:
        print("Creating new admin2...")
        admin2 = User(
            username='admin2',
            full_name='Backup Administrator',
            role='admin',
            department='Administration',
            is_active=True
        )
        admin2.set_password('admin123')
        db.session.add(admin2)
        print("  - Created new admin2.")

    db.session.commit()
    print("\nSUCCESS!")
    print("New admin: username='admin2', password='admin123', role=admin")
    print("1. Run 'python app.py' (restart if running)")
    print("2. Login: http://127.0.0.1:5000/login")
    print("   - Username: admin2")
    print("   - Password: admin123")
    print("   - Select: Administrator role")
    print("\nTip: Also run 'python check_admin.py' to verify.")

