# TODO

## Subject field + repeat submissions
- [ ] Update evaluation DB model to include `subject` column
- [ ] Update `database/schema.sql` to add `subject` column to `evaluations`
- [ ] Update `EvaluationForm` (routes/student.py) to add `subject` free-text field
- [ ] Update `templates/student/evaluate.html` to render subject input
- [ ] Update submission handler to save `subject` into Evaluation
- [ ] Allow students to evaluate same instructor multiple times per semester (remove existing duplicate-blocking logic)
- [ ] Create/update confirmation/history UI text if needed (no logic changes expected)
- [ ] Run a quick smoke test: start app, submit two evaluations for same faculty, verify stored records

