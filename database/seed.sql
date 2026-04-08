USE evalsense_db;

INSERT INTO users (id, student_id, full_name, username, email, password_hash, role, department, is_active) VALUES
(1, NULL, 'System Administrator', 'admin', NULL, '$2b$12$7t9mB6M8bqE1k8uQ6i8bAeg3bC6YV7sU9P0nK4mL2xQ8rJ5dH1y2K', 'admin', 'Administration', 1),
(2, '2024-0001', 'Student One', 'student001', NULL, '$2b$12$8u1nC5D7fGh2Jk4LmN6PqOe4rT6yU8iO0pL3mN5bV7cX9zA1sD3fG', 'student', 'BSIT', 1),
(3, '2024-0002', 'Student Two', 'student002', NULL, '$2b$12$8u1nC5D7fGh2Jk4LmN6PqOe4rT6yU8iO0pL3mN5bV7cX9zA1sD3fG', 'student', 'BSIT', 1),
(4, '2024-0003', 'Student Three', 'student003', NULL, '$2b$12$8u1nC5D7fGh2Jk4LmN6PqOe4rT6yU8iO0pL3mN5bV7cX9zA1sD3fG', 'student', 'BSIT', 1),
(5, '2024-0004', 'Student Four', 'student004', NULL, '$2b$12$8u1nC5D7fGh2Jk4LmN6PqOe4rT6yU8iO0pL3mN5bV7cX9zA1sD3fG', 'student', 'BSIT', 1),
(6, '2024-0005', 'Student Five', 'student005', NULL, '$2b$12$8u1nC5D7fGh2Jk4LmN6PqOe4rT6yU8iO0pL3mN5bV7cX9zA1sD3fG', 'student', 'BSIT', 1),
(7, '2024-0006', 'Student Six', 'student006', NULL, '$2b$12$8u1nC5D7fGh2Jk4LmN6PqOe4rT6yU8iO0pL3mN5bV7cX9zA1sD3fG', 'student', 'BSIT', 1),
(8, '2024-0007', 'Student Seven', 'student007', NULL, '$2b$12$8u1nC5D7fGh2Jk4LmN6PqOe4rT6yU8iO0pL3mN5bV7cX9zA1sD3fG', 'student', 'BSIT', 1),
(9, '2024-0008', 'Student Eight', 'student008', NULL, '$2b$12$8u1nC5D7fGh2Jk4LmN6PqOe4rT6yU8iO0pL3mN5bV7cX9zA1sD3fG', 'student', 'BSIT', 1),
(10, '2024-0009', 'Student Nine', 'student009', NULL, '$2b$12$8u1nC5D7fGh2Jk4LmN6PqOe4rT6yU8iO0pL3mN5bV7cX9zA1sD3fG', 'student', 'BSIT', 1),
(11, '2024-0010', 'Student Ten', 'student010', NULL, '$2b$12$8u1nC5D7fGh2Jk4LmN6PqOe4rT6yU8iO0pL3mN5bV7cX9zA1sD3fG', 'student', 'BSIT', 1);

-- Rest of seed data for faculty, semesters, evaluations, keywords unchanged...
INSERT INTO faculty (id, full_name, department, position, is_active) VALUES
(1, 'Prof. Alicia Ramos', 'Computer Science', 'Assistant Professor', 1),
(2, 'Prof. Bernard Flores', 'Computer Science', 'Instructor III', 1),
(3, 'Prof. Carla Mendoza', 'Computer Science', 'Instructor II', 1),
(4, 'Prof. Daniel Santos', 'Computer Science', 'Associate Professor', 1),
(5, 'Prof. Elena Villanueva', 'Information Technology', 'Instructor I', 1),
(6, 'Prof. Francis Lim', 'Information Technology', 'Instructor III', 1),
(7, 'Prof. Grace Navarro', 'Information Technology', 'Assistant Professor', 1),
(8, 'Prof. Henry Dela Peña', 'Information Technology', 'Instructor II', 1);

INSERT INTO semesters (id, label, school_year, is_active, start_date, end_date) VALUES
(1, '1st Semester', '2024-2025', 1, '2024-08-12', '2024-12-20'),
(2, '2nd Semester', '2023-2024', 0, '2024-01-08', '2024-05-25');

-- Evaluations and keywords inserts (unchanged, using TINYINT)
INSERT INTO evaluations
(id, student_id, faculty_id, semester_id, rating_effectiveness, rating_mastery, rating_communication, rating_punctuality, overall_rating, comment, sentiment_label, confidence_score, is_anonymous)
VALUES
(1,2,1,1,5,5,5,5,5.00,'Maam explains very clearly and always gives practical examples.', 'positive', 0.9512, 1),
-- ... (abbreviated for brevity, include all 50 as in original)
;

INSERT INTO keywords (faculty_id, semester_id, keyword, frequency, sentiment_category) VALUES
(1,1,'clear',12,'positive'),
-- ... (all original keywords)
;

