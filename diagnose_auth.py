from app import app, db
from models.user import User


with app.app_context():
    print("=== Auth Diagnosis ===")
    # Note: if this is not a real table in your DB, adjust accordingly.
    try:
        has_user_table = db.engine.dialect.has_table(db.engine, "users")
    except Exception:
        has_user_table = "unknown"
    print("User table exists:", has_user_table)

    test_admin_pw = "admin123"
    test_student_pw = "student123"

    changed = False

    # Check/create admin
    admin = User.query.filter_by(username="admin").first()
    if admin:
        print(f"Admin found: {admin.username}, active: {admin.is_active}")
        if not admin.check_password(test_admin_pw):
            print("  Admin password mismatch; resetting...")
            admin.set_password(test_admin_pw)
            changed = True
    else:
        print("No admin found; creating...")
        admin = User(
            username="admin",
            full_name="Admin",
            role="admin",
            department="Administration",
            is_active=True,
        )
        admin.set_password(test_admin_pw)
        db.session.add(admin)
        changed = True

    # Check/create student001
    student = User.query.filter_by(username="student001").first()
    if student:
        print(f"Student001 found: {student.username}, active: {student.is_active}")
        if not student.check_password(test_student_pw):
            print("  Student password mismatch; resetting...")
            student.set_password(test_student_pw)
            changed = True
    else:
        print("No student001 found; creating...")
        student = User(
            student_id="2024-0001",
            full_name="Test Student",
            username="student001",
            role="student",
            department="BSIT",
            is_active=True,
        )
        student.set_password(test_student_pw)
        db.session.add(student)
        changed = True

    if changed:
        db.session.commit()
        print("Changes committed.")

    print("\n=== Test Results ===")
    print("admin/admin123 should work now")
    print("student001/student123 or 2024-0001/student123 should work")
    print("Restart app.py if running, then test login at http://127.0.0.1:5000")

