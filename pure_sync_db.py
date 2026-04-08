from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models.user import User
from models.faculty import Faculty
from models.semester import Semester
from models.evaluation import Evaluation, Keyword

db = SQLAlchemy()

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.drop_all()
    db.create_all()
    print("Database tables recreated successfully matching models.")
