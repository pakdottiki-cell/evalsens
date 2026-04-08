# EvalSense: A Machine Learning-Based Sentiment Analysis System for Faculty Evaluation

EvalSense is a production-ready web-based capstone project for **Buenavista Community College, Buenavista, Bohol, Philippines**. It automates faculty evaluation by combining structured student ratings with machine learning-based sentiment analysis of written student feedback.

## Features

- Student and administrator authentication
- Role-based access control
- Faculty evaluation with star ratings
- Sentiment analysis using machine learning
- Keyword extraction and word cloud generation
- Semester-based dashboards and reports
- Faculty performance analytics with Chart.js
- PDF export for faculty reports
- Secure password hashing using bcrypt
- CSRF-protected forms using Flask-WTF
- Session timeout after 30 minutes of inactivity

## Prerequisites

Before running the project, make sure you have:

- Python 3.10+
- MySQL Server
- pip
- virtualenv or venv

## Installation Guide

### a. Clone the repository

```bash
git clone https://github.com/your-username/evalsense.git
cd evalsense
```plaintext

### b. Create a virtual environment

```bash
python -m venv venv
```plaintext

Activate it:

**Windows**
```bash
venv\Scripts\activate
```plaintext

**Linux/macOS**
```bash
source venv/bin/activate
```plaintext

### c. Install dependencies

```bash
pip install -r requirements.txt
```plaintext

### d. Download NLTK data

Run Python shell:

```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('omw-1.4')
```plaintext

### e. Create `.env` file

Create a file named `.env` in the project root:

```env
SECRET_KEY=change-this-to-a-secure-random-secret
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=evalsense_db
DATABASE_URL=mysql+mysqlconnector://root:your_mysql_password@localhost:3306/evalsense_db
```plaintext

### f. Create MySQL database

```sql
CREATE DATABASE evalsense_db;
```plaintext

### g. Run `schema.sql` to create tables

```bash
mysql -u root -p evalsense_db < database/schema.sql
```plaintext

### h. Run `seed.sql` to insert sample data

```bash
mysql -u root -p evalsense_db < database/seed.sql
```plaintext

### i. Train the ML model

```bash
python ml/train_model.py
```plaintext

This will generate:

- `ml/model.pkl`
- `ml/vectorizer.pkl`

### j. Run the application

```bash
python app.py
```plaintext

Open in browser:

```text
http://127.0.0.1:5000
```plaintext

---

## Default Login Credentials

### Admin
- **Username:** `admin`
- **Password:** `admin123`

### Student
- **Username:** `student001`
- **Password:** `student123`

> On first app start, the system securely syncs default account passwords using bcrypt.

---

## Project Structure

```text
evalsense/
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── database/
│   ├── schema.sql
│   └── seed.sql
├── ml/
│   ├── train_model.py
│   ├── predict.py
│   ├── preprocess.py
│   └── dataset.csv
├── models/
│   ├── user.py
│   ├── faculty.py
│   ├── evaluation.py
│   └── semester.py
├── routes/
│   ├── auth.py
│   ├── student.py
│   ├── admin.py
│   └── api.py
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   └── img/
│       └── wordclouds/
├── templates/
│   ├── base.html
│   ├── auth/
│   │   └── login.html
│   ├── student/
│   │   ├── dashboard.html
│   │   ├── evaluate.html
│   │   └── confirmation.html
│   └── admin/
│       ├── dashboard.html
│       ├── sentiment.html
│       ├── reports.html
│       ├── faculty.html
│       └── keywords.html
└── utils/
    ├── pdf_generator.py
    └── keyword_extractor.py
```plaintext

---

## How to Generate PDF Reports

1. Log in as administrator
2. Open **Faculty Reports**
3. Select semester
4. Click **Download PDF** for individual faculty
5. Or click **Download All Reports**

PDF output contains:

- BCC letterhead
- report title
- generated date
- faculty information
- criterion ratings
- sentiment summary
- keywords
- sample comments
- signature lines

---

## How to Retrain the ML Model with New Data

1. Update `ml/dataset.csv`
2. Ensure it contains:
   - `comment`
   - `sentiment`
3. Retrain the model:

```bash
python ml/train_model.py
```plaintext

This replaces the saved classifier and vectorizer.

---

## Troubleshooting

### 1. MySQL connection error
- Check `.env` credentials
- Ensure MySQL service is running
- Confirm database exists

### 2. `ModuleNotFoundError`
- Activate the virtual environment
- Reinstall requirements:
  ```bash
  pip install -r requirements.txt
  ```plaintext

### 3. NLTK resource missing
Run:

```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('omw-1.4')
```plaintext

### 4. Model files missing
Run:

```bash
python ml/train_model.py
```plaintext

### 5. CSRF token missing
- Refresh the page
- Ensure cookies are enabled
- Do not submit expired sessions

### 6. Session automatically logs out
- This is expected after 30 minutes of inactivity

---

## Academic Use

This system is designed for capstone and academic demonstration purposes, but the architecture is also suitable for real institutional deployment with further hardening and scaling.