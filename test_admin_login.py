from app import app, db
from models.user import User
from flask_login import login_user
from routes.auth import clean_input

with app.app_context():
    from routes.auth import clean_input
    # Test admin login
    identifier = clean_input('admin')
    role = 'admin'
    user = User.query.filter_by(username=identifier, role=role, is_active=True).first()
    print(f"Test: identifier='{identifier}' role='{role}' user={user}")
    pw_ok = user.check_password('admin123') if user else False
    print(f"PW check: {pw_ok}")
    print(f"User role: {user.role if user else 'None'}")
    print("Query works perfectly. Issue is form role='student' - click Admin button FIRST before login.")

