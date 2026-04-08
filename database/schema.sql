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
    rating_effectiveness INT NOT NULL,
    rating_mastery INT NOT NULL,
    rating_communication INT NOT NULL,
    rating_punctuality INT NOT NULL,
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
