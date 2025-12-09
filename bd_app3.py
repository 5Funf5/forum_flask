from flask_sqlalchemy import SQLAlchemy
from config import CONFIG
from datetime import datetime
db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    admin = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now().replace(microsecond=0))
    
    # Relationships
    categories = db.relationship('Category', backref='author', lazy=True)
    topics = db.relationship('Topic', backref='author', lazy=True)
    posts = db.relationship('Post', backref='author', lazy=True)
    
    def __repr__(self):
        return f'{self.username}'

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now().replace(microsecond=0))
    
    # Relationships
    topics = db.relationship('Topic', backref='category', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'{self.name}'

class Topic(db.Model):
    __tablename__ = 'topics'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now().replace(microsecond=0))
    
    # Relationships
    
    posts = db.relationship('Post', backref='topic', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Topic {self.title}>'

class Post(db.Model):
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now().replace(microsecond=0))
    
    def __repr__(self):
        return f'{self.id}'



class DataBase:
    
    def __init__(self, app=None):
        """Инициализация базы данных"""
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Инициализация приложения Flask"""
        app.config['SQLALCHEMY_DATABASE_URI'] = CONFIG.SQLALCHEMY_DATABASE_URI
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = CONFIG.SQLALCHEMY_TRACK_MODIFICATIONS
        
        db.init_app(app)
        
        with app.app_context():
            db.create_all()

if __name__ == "__main__":
    from flask import Flask
    app = Flask(__name__)
    
    database = DataBase(app)
    
    # Теперь можно работать с БД в контексте приложения
    with app.app_context():
        
        print(User.query.all())