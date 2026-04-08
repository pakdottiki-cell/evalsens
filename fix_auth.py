from app import app, db, bcrypt
from models.user import User

with app.app_context():
    print("=== Fixing Invalid Credentials ===")
    
    # Test DB connectivity
    try:
        from sqlalchemy import text
        result = db.session.execute(text("SELECT 1")).scalar()
        print("DB connection OK")
    except Exception as e:
        print("DB error:", e)
        sys.exit(1)
    
    test_admin_pw = 'admin123'
    test_student_pw = 'student123'
    
    # Admin
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            full_name='System Admin',
            role='admin',
            department='Administration',
            is_active=True
        )
        db.session.add(admin)
        print("Created admin user")
    admin.set_password(test_admin_pw)
    admin.is_active = True
    print(f"Admin '{admin.username}' password set to '{test_admin_pw}'")
    
    # Student
    student = User.query.filter_by(username='student001').first()
    if not student:
        student = User(
            student_id='2024-0001',
            username='student001',
            full_name='Test Student',
            role='student',
            department='BSIT',
            is_active=True
        )
        db.session.add(student)
        print("Created student001 user")
    student.set_password(test_student_pw)
    student.is_active = True
    print(f"Student '{student.username}' password set to '{test_student_pw}'")
    
    db.session.commit()
    print("\nSUCCESS: Users updated!")
    print("1. CTRL+C app.py server, then rerun 'python app.py'")
    print("2. Test login:")
    print("   - Admin: Role=Administrator, Username=admin, Password=admin123")
    print("   - Student: Role=Student, Username=student001 or 2024-0001, Password=student123")
    print("3. If still fails, share MySQL query output & app logs")

