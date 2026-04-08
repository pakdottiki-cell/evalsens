from app import app, bcrypt
from models.user import User

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    print("Admin user details:")
    if admin:
        print(f" - ID: {admin.id}")
        print(f" - Role: {admin.role}")
        print(f" - Active: {admin.is_active}")
        print(f" - Hash preview: {admin.password_hash[:50]}...")
        print(f" - check_password('admin123'): {admin.check_password('admin123')}")
    else:
        print("No admin user found")
    
    print("\nQuery test for login:")
    print("Admin query:", User.query.filter_by(username='admin', role='admin', is_active=True).first() is not None)
    print("Ready for login test.")

    # Check admin2
    admin2 = User.query.filter_by(username='admin2').first()
    print("\nAdmin2 user details:")
    if admin2:
        print(f" - ID: {admin2.id}")
        print(f" - Role: {admin2.role}")
        print(f" - Active: {admin2.is_active}")
        print(f" - Hash preview: {admin2.password_hash[:50]}...")
        print(f" - check_password('admin123'): {admin2.check_password('admin123')}")
    else:
        print("No admin2 user found")

    print("\nAdmin2 query test:", User.query.filter_by(username='admin2', role='admin', is_active=True).first() is not None)


