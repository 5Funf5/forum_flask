from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///forum.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Модели базы данных
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship('Post', backref='author', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    topics = db.relationship('Topic', backref='category', lazy=True)

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    posts = db.relationship('Post', backref='topic', lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)

# Создание таблиц
with app.app_context():
    db.create_all()
    
    # Создание тестовых категорий если их нет
    if Category.query.count() == 0:
        categories = [
            Category(name="Общие обсуждения", description="Общие темы для обсуждения"),
            Category(name="Технологии", description="Обсуждение технологий и программирования"),
            Category(name="Игры", description="Все о компьютерных играх"),
            Category(name="Помощь", description="Помощь и поддержка")
        ]
        db.session.bulk_save_objects(categories)
        db.session.commit()

# Маршруты
@app.route('/')
def index():
    categories = Category.query.all()
    recent_topics = Topic.query.order_by(Topic.created_at.desc()).limit(5).all()
    return render_template('index.html', categories=categories, recent_topics=recent_topics)

@app.route('/category/<int:category_id>')
def category(category_id):
    category = Category.query.get_or_404(category_id)
    topics = Topic.query.filter_by(category_id=category_id).order_by(Topic.created_at.desc()).all()
    return render_template('category.html', category=category, topics=topics)

@app.route('/topic/<int:topic_id>')
def topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    posts = Post.query.filter_by(topic_id=topic_id).order_by(Post.created_at.asc()).all()
    return render_template('topic.html', topic=topic, posts=posts)

@app.route('/create_topic', methods=['GET', 'POST'])
def create_topic():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему чтобы создать тему')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category_id = request.form['category_id']
        
        topic = Topic(
            title=title,
            content=content,
            user_id=session['user_id'],
            category_id=category_id
        )
        db.session.add(topic)
        db.session.commit()
        
        flash('Тема успешно создана!')
        return redirect(url_for('topic', topic_id=topic.id))
    
    categories = Category.query.all()
    return render_template('create_topic.html', categories=categories)

@app.route('/topic/<int:topic_id>/reply', methods=['POST'])
def reply(topic_id):
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему чтобы оставить ответ')
        return redirect(url_for('login'))
    
    content = request.form['content']
    post = Post(
        content=content,
        user_id=session['user_id'],
        topic_id=topic_id
    )
    db.session.add(post)
    db.session.commit()
    
    flash('Ответ добавлен!')
    return redirect(url_for('topic', topic_id=topic_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Это имя пользователя уже занято')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Этот email уже используется')
            return redirect(url_for('register'))
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Регистрация успешна! Теперь вы можете войти.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Вы успешно вошли в систему!')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы')
    return redirect(url_for('index'))

@app.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    user_topics = Topic.query.filter_by(user_id=user.id).order_by(Topic.created_at.desc()).limit(10).all()
    user_posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).limit(10).all()
    return render_template('profile.html', user=user, topics=user_topics, posts=user_posts)

if __name__ == '__main__':
    app.run(debug=True)