from flask import current_app
from app import db
from models.user import User


def setup_test_users():
    """Create/verify test users.

    Called from app.py at startup.
    """
    # `app` is already created in app.py; just use the current app context.
    # When called from app.py startup, this function is invoked inside `with app.app_context()`.
    # So we don't re-import `app` (which can create import cycles).
    with current_app.app_context():
        test_admin_pw = "admin123"
        test_student_pw = "student123"

        changed = False

        # Admin
        admin = User.query.filter_by(username="admin").first()
        if admin:
            if not admin.check_password(test_admin_pw):
                admin.set_password(test_admin_pw)
                admin.role = "admin"
                admin.is_active = True
                admin.department = admin.department or "Administration"
                changed = True
        else:
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

        # Students (student001..student010)
        # Match database/seed.sql sample IDs:
        #  - student001 -> 2024-0001
        #  - ...
        #  - student010 -> 2024-0010
        for i in range(1, 11):
            uname = f"student{i:03d}"
            sid = f"2024-{i:04d}"
            full_name = f"Test Student {i:02d}"
            department = "BSIT"

            student = User.query.filter_by(username=uname).first()
            if student:
                if not student.check_password(test_student_pw):
                    student.set_password(test_student_pw)
                    student.role = "student"
                    student.is_active = True
                    student.department = student.department or department
                    changed = True
                # Ensure student_id is set if model/schema supports it
                if not student.student_id:
                    student.student_id = sid
                    changed = True
            else:
                student = User(
                    student_id=sid,
                    full_name=full_name,
                    username=uname,
                    role="student",
                    department=department,
                    is_active=True,
                )
                student.set_password(test_student_pw)
                db.session.add(student)
                changed = True

        if changed:
            db.session.commit()


if __name__ == "__main__":
    setup_test_users()

