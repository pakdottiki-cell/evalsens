"""Create the first administrator with a password entered interactively.

Run once after configuring the database: ``python bootstrap_admin.py``.
This refuses to run if an administrator already exists.
"""

from getpass import getpass

from app import app, db
from models.user import User


def main():
    with app.app_context():
        if User.query.filter_by(role="admin").first():
            print("An administrator already exists; no account was changed.")
            return 1

        username = input("Admin username: ").strip()
        full_name = input("Admin full name: ").strip()
        if len(username) < 3 or len(username) > 50 or len(full_name) < 2 or len(full_name) > 100:
            print("Username must be 3–50 characters and full name 2–100 characters.")
            return 1
        if User.query.filter_by(username=username).first():
            print("That username is already in use.")
            return 1

        password = getpass("Admin password (at least 14 characters): ")
        confirmation = getpass("Confirm password: ")
        if len(password) < 14 or len(password) > 128 or len(password.encode("utf-8")) > 72 or password != confirmation:
            print("Passwords must match, contain 14–128 characters, and use no more than 72 UTF-8 bytes.")
            return 1

        admin = User(
            username=username,
            full_name=full_name,
            role="admin",
            department="Administration",
            is_active=True,
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print("Administrator created.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
