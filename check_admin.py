"""Show administrator account status without exposing password hashes."""

from app import app
from models.user import User


with app.app_context():
    admins = User.query.filter_by(role="admin").order_by(User.username.asc()).all()
    if not admins:
        print("No administrator accounts found. Run: python bootstrap_admin.py")
    for admin in admins:
        print(f"{admin.username}: {'active' if admin.is_active else 'inactive'}")
