import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    ENV = os.getenv("FLASK_ENV", "production").lower()
    IS_PRODUCTION = ENV == "production"

    SECRET_KEY = os.getenv("SECRET_KEY")
    if IS_PRODUCTION and (not SECRET_KEY or SECRET_KEY.strip() in {"", "dev-secret-change-this", "changeme"}):
        raise RuntimeError(
            "Insecure SECRET_KEY detected. Set a strong SECRET_KEY in environment for production."
        )
    if not SECRET_KEY:
        SECRET_KEY = "dev-secret-change-this"

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"mysql+mysqlconnector://{os.getenv('MYSQL_USER', 'root')}:{os.getenv('MYSQL_PASSWORD', '')}"
        f"@{os.getenv('MYSQL_HOST', 'localhost')}:{os.getenv('MYSQL_PORT', '3306')}"
        f"/{os.getenv('MYSQL_DB', 'evalsense_db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_TIMEOUT = 1800
    PERMANENT_SESSION_LIFETIME = timedelta(seconds=SESSION_TIMEOUT)

    ML_MODEL_PATH = "ml/model.pkl"
    ML_VECTORIZER_PATH = "ml/vectorizer.pkl"
    UPLOAD_FOLDER = "static/img/wordclouds"
    PDF_OUTPUT_FOLDER = "static/reports"

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = IS_PRODUCTION
    REMEMBER_COOKIE_SECURE = IS_PRODUCTION

    # Proxy-aware secure request handling (useful behind reverse proxies).
    PREFERRED_URL_SCHEME = "https" if IS_PRODUCTION else "http"

    # Optional model artifact integrity checks (SHA-256 hex digests).
    MODEL_SHA256 = os.getenv("MODEL_SHA256")
    VECTORIZER_SHA256 = os.getenv("VECTORIZER_SHA256")
