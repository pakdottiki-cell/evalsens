# Revert All AI Changes

## Steps:
- [x] 1. Delete templates/auth/register.html
- [x] 2. Revert templates/auth/login.html (remove register link)
- [x] 3. Revert routes/auth.py (remove RegisterForm and /register route)
- [x] 4. Revert app.py sync_default_accounts (only set_password if new user)
- [ ] 5. Revert models/user.py check_password (standard bcrypt no try/except)
- [ ] 6. Delete all TODO*.md files
- [ ] 7. Test `python app.py` and login admin/admin123
- [ ] 8. Complete
