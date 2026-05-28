# TODO - Update Faculty Evaluation Form

## Plan Summary
Replace the evaluation form instrument:
- A) Instructional Skills: 18 statements
- B) Personal and Social Qualities: 9 statements

Each statement uses the 5-point scale:
- Outstanding=5, Very satisfactory=4, Satisfactory=3, Fair=2, Poor=1

## Implementation Steps
1. DB + model: add 27 integer columns to `Evaluation` (Instructional 18 + Personal/Social 9) and update schema.sql.
2. WTForms: update `routes/student.py` EvaluationForm to include 27 RadioFields and save them.
3. Template: update `templates/student/evaluate.html` to render A(18) and B(9) statements.
4. Admin/API/PDF: update derived averages and any visuals that reference old 4-category ratings.
5. Smoke test: submit evaluation + render admin reports.

## Progress
- [x] Reviewed current evaluation form/template/model.
- [x] Confirmed DB schema currently has only 4 category ratings.
- [x] Chose to store values as Option 2 (DB columns).
- [x] Step 1: Update DB schema.sql + models/evaluation.py.
- [x] Step 2: Update routes/student.py (form + save + overall).

- [x] Step 3: Update templates/student/evaluate.html.

- [x] Step 4: Update admin/utils/api/pdf/templates to use new derived averages.
- [ ] Step 5: Run smoke test.
- [ ] Step 6: Ensure schema.sql/model align with deployed DB (recreate tables if needed).





