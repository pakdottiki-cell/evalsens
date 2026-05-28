CREATE DATABASE IF NOT EXISTS evalsense_db;
USE evalsense_db;

DROP TABLE IF EXISTS keywords;
DROP TABLE IF EXISTS evaluations;
DROP TABLE IF EXISTS semesters;
DROP TABLE IF EXISTS faculty;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id VARCHAR(20) UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    role VARCHAR(20) DEFAULT 'student' NOT NULL,
    department VARCHAR(50) NOT NULL,
    is_active TINYINT(1) DEFAULT 1,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE faculty (
    id INT PRIMARY KEY AUTO_INCREMENT,
    full_name VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    position VARCHAR(100),
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE semesters (
    id INT PRIMARY KEY AUTO_INCREMENT,
    label VARCHAR(20),
    school_year VARCHAR(20),
    is_active TINYINT(1) DEFAULT 0,
    start_date DATE,
    end_date DATE
);

CREATE TABLE evaluations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    faculty_id INT NOT NULL,
    semester_id INT NOT NULL,
    -- A) Instructional Skills (18 items)
    is_1 INT NOT NULL,
    is_2 INT NOT NULL,
    is_3 INT NOT NULL,
    is_4 INT NOT NULL,
    is_5 INT NOT NULL,
    is_6 INT NOT NULL,
    is_7 INT NOT NULL,
    is_8 INT NOT NULL,
    is_9 INT NOT NULL,
    is_10 INT NOT NULL,
    is_11 INT NOT NULL,
    is_12 INT NOT NULL,
    is_13 INT NOT NULL,
    is_14 INT NOT NULL,
    is_15 INT NOT NULL,
    is_16 INT NOT NULL,
    is_17 INT NOT NULL,
    is_18 INT NOT NULL,

    -- B) Personal and Social Qualities (9 items)
    ps_1 INT NOT NULL,
    ps_2 INT NOT NULL,
    ps_3 INT NOT NULL,
    ps_4 INT NOT NULL,
    ps_5 INT NOT NULL,
    ps_6 INT NOT NULL,
    ps_7 INT NOT NULL,
    ps_8 INT NOT NULL,
    ps_9 INT NOT NULL,

    overall_rating DECIMAL(3,2) NOT NULL,
    comment TEXT NOT NULL,
    sentiment_label ENUM('positive','negative','neutral') NOT NULL,
    confidence_score DECIMAL(5,4) NOT NULL,
    is_anonymous TINYINT(1) DEFAULT 1,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_eval_student FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_eval_faculty FOREIGN KEY (faculty_id) REFERENCES faculty(id) ON DELETE CASCADE,
    CONSTRAINT fk_eval_semester FOREIGN KEY (semester_id) REFERENCES semesters(id) ON DELETE CASCADE
);

CREATE TABLE keywords (
    id INT PRIMARY KEY AUTO_INCREMENT,
    faculty_id INT NOT NULL,
    semester_id INT NOT NULL,
    keyword VARCHAR(100) NOT NULL,
    frequency INT NOT NULL DEFAULT 0,
    sentiment_category ENUM('positive','negative','neutral') NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_keyword (faculty_id, semester_id, keyword, sentiment_category),
    CONSTRAINT fk_keyword_faculty FOREIGN KEY (faculty_id) REFERENCES faculty(id) ON DELETE CASCADE,
    CONSTRAINT fk_keyword_semester FOREIGN KEY (semester_id) REFERENCES semesters(id) ON DELETE CASCADE
);
