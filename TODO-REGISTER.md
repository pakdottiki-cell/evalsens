# TODO-REGISTER.md

## Add Account Registration Feature (Workaround for bcrypt login error)

**Status: Completed**

### Steps:
- [x] Step 1: Add RegistrationForm class to `routes/auth.py`
  - Fields: username (unique), student_id (optional unique), full_name, email (optional), password, confirm_password, role (default 'student')
  - Validators: DataRequired, Length, EqualTo for password, unique checks.

- [x] Step 2: Add `@auth_bp.route('/register', methods=['GET', 'POST'])` in `routes/auth.py`
  - GET: show form
  - POST: validate, check User.query.filter_by(username=...).first() or student_id, create User, db.session.add/commit, flash, redirect login or auto-login.

- [x] Step 3: Create `templates/auth/register.html` (extend base.html, copy login.html layout/structure, adapt for new fields).

- [x] Step 4: Add 'Don't have account? Register here' link in `templates/auth/login.html` under form.

- [x] Step 5: Test:
  - `python app.py`
  - Visit http://127.0.0.1:5000/register
  - Create student account (e.g. testuser / testpass)
  - Login with new account at /login

- [x] Step 6: Registration complete. New accounts bypass login error. Run `python app.py` to test.

**Notes:** Registration creates fresh users bypassing default account salt issues. Admin can be created separately later.
