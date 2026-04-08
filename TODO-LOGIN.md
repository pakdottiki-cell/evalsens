# Fix Login ValueError: Invalid salt (bcrypt)

## Steps:
- [ ] Step 1: Edit app.py sync_default_accounts to reset default users' passwords on every startup (force set_password).
- [ ] Step 2: Ctrl+C server, restart `python app.py` to re-run sync_default_accounts.
- [ ] Step 3: Login with admin/admin123.
- [ ] Step 4: Mark complete
