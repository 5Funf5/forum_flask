from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

class CONFIG:
    db = 'forum.db'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{db}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = CONFIG.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = CONFIG.SQLALCHEMY_TRACK_MODIFICATIONS
db = SQLAlchemy(app)



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

def create_db():
    app.app_context().push()
    db.create_all()
    
@app.route('/', methods=['GET', 'POST'])
def index():
    
    categories = Category.query.all()
    for categories_id in categories:
        categories_id.topic_count = len(Topic.query.filter(Topic.category_id==categories_id.id).all())
        post_all = Topic.query.filter(Topic.category_id==categories_id.id).all()
        categories_id.post_count = 0
        for post_id in post_all:
            number = len(Post.query.filter(Post.topic_id==post_id.id).all())
            categories_id.post_count = categories_id.post_count + number
    return render_template('index.html', categories=categories)


@app.route('/profile/')
@app.route('/profile/<string:username>')
def profile(username=None):
    # Если username не указан, показываем профиль текущего пользователя
    if username is None:
        if 'user_id' not in session:
            flash('Для просмотра профиля необходимо войти в систему')
            return redirect(url_for('login'))
        user_id = session['user_id']
        user = User.query.get(user_id)
        if not user:
            flash('Пользователь не найден')
            return redirect(url_for('login'))
    else:
        # Ищем пользователя по username
        user = User.query.filter(User.username == username).first()
        if not user:
            flash('Пользователь не найден')
            return redirect(url_for('index'))  # или куда-то еще
    
    # Общая логика для обоих случаев
    user.is_online = session.get('online', False) if username is None else False
    user.post_count = len(Post.query.filter(Post.user_id==user.id).all())
    user.topic_count = len(Topic.query.filter(Topic.user_id==user.id).all())
    user.reputation = 10
    
    recent_posts = Post.query\
        .join(Topic, Post.topic_id == Topic.id)\
        .add_columns(
            Post.id,
            Post.content,
            Post.created_at,
            Post.topic_id,
            Topic.title.label('topic_title')
        )\
        .filter(Post.user_id==user.id)\
        .limit(5)\
        .all()
    
    return render_template('profile.html', user=user, recent_posts=recent_posts)

@app.route('/login', methods=['GET'])
def login_page():
    if session:
        # flash('Как ты это сделал?')
        # return redirect(url_for('index'))
        pass
        form_type = request.args.get('form', 'login')
        return render_template('login.html', form_type=form_type)
    else:
        form_type = request.args.get('form', 'login')
        return render_template('login.html', form_type=form_type)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.form.get('form_type') == 'login':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Проверка пользователя

        if username and password:
            user = User.query.filter_by(username=username, password=password).first()
            
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['online'] = 'online'

            flash('Вы успешно вошли в систему!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')
            return redirect(url_for('login_page', form='login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.form.get('form_type') == 'register':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Валидация
        if password != confirm_password:
            flash('Пароли не совпадают', 'error')
            return redirect(url_for('login_page', form='register'))
        
        existing_user = User.query.filter(
                (User.username == username) | (User.email == email)
            ).first()
            
        if existing_user:
            flash('Ошибка регистрации. Пользователь уже существует.', 'error')
            return redirect(url_for('login_page', form='register'))
        # Создание пользователя
        user = User(
                username=username,
                email=email,
                password=password
            )
        db.session.add(user)
        db.session.commit()
        flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
        return redirect(url_for('login_page', form='login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы')
    return redirect(url_for('index'))

@app.route('/about', methods=['GET', 'POST'])
def about():
    class stats:
        users = len(User.query.all())
        topics = len(Topic.query.all())
        posts = len(Post.query.all())
        last_post = Post.query\
        .order_by(Post.created_at)\
        .first()
        if last_post is not None:
            last_post = datetime.today().date()
        
    return render_template('about.html', stats=stats)

@app.route('/category/<int:category_id>', methods=['GET', 'POST'])
def category(category_id):
    category = Category.query.get(category_id)
    
    topics = Topic.query.filter(Topic.category_id == category_id)
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'delete':
            topic_id = request.form.get('topic_id')
            delete_topic = Topic.query.get(topic_id)
            if delete_topic:
                db.session.delete(delete_topic)
                db.session.commit()
                flash('Категория удалена')
        else:
            content = request.form['content']
            title = request.form['title']

            user_id = session['user_id']
            topic = Topic(content=content, user_id=user_id, category_id=category_id,title=title)
            db.session.add(topic)
            db.session.commit()
            flash('Вы создали тему')
    return render_template('category.html',category=category,topics=topics)

@app.route('/topic/<int:topic_id>', methods=['GET', 'POST'])
def topic(topic_id):
    topic = Topic.query.get(topic_id)
    posts = Post.query\
            .join(User, Post.user_id == User.id)\
            .join(Topic, Post.topic_id == Topic.id)\
            .add_columns(Post.id, Post.content, Post.created_at, User.username, Topic.title)\
            .filter(Post.topic_id == topic_id)
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'delete':
            post_id = request.form.get('post_id')
            delete_post = Post.query.get(post_id)
            if delete_post:
                db.session.delete(delete_post)
                db.session.commit()
                flash('Сообщение удалено')
        else:
            content = request.form['content']
            user_id = session['user_id']
            post = Post(content=content, user_id=user_id, topic_id=topic_id)
            db.session.add(post)
            db.session.commit()
            flash('Вы отправили сообщение')
    return render_template('topic.html', topic=topic, posts=posts)
        
from flask import Flask, render_template, session, redirect, url_for
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        # Проверка прав администратора (замените на свою логику)
        # flash('Доступ запрещен. Требуются права администратора.', 'error')
        # return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@admin_required
def admin_dashboard():
    return render_template('admin/admin_dashboard.html')

@app.route('/admin/users')
@admin_required
def admin_users():
    return render_template('admin/admin_users.html')

@app.route('/admin/topics')
@admin_required
def admin_topics():
    return render_template('admin/admin_topics.html')

@app.route('/admin/posts')
@admin_required
def admin_posts():
    return render_template('admin/admin_posts.html')

@app.route('/admin/categories')
@admin_required
def admin_categories():
    return render_template('admin/admin_categories.html')

@app.route('/admin/moderation')
@admin_required
def admin_moderation():
    return render_template('admin/admin_moderation.html')

@app.route('/admin/settings')
@admin_required
def admin_settings():
    return render_template('admin/admin_settings.html')        
        
        
        
        
        
        
    
if __name__ == '__main__':

    app.run(debug=True)
    