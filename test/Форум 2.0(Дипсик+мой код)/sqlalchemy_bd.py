from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class CONFIG:
    db = 'forum.db'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{db}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    admin = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    categories = db.relationship('Category', backref='author', lazy=True)
    topics = db.relationship('Topic', backref='author', lazy=True)
    posts = db.relationship('Post', backref='author', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    topics = db.relationship('Topic', backref='category', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Topic(db.Model):
    __tablename__ = 'topics'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Post {self.id}>'

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
    
    def create_category(self, name, description, user_id):
        """Создание новой категории"""
        try:
            category = Category(
                name=name,
                description=description,
                user_id=user_id
            )
            db.session.add(category)
            db.session.commit()
            return category.id
        except Exception as e:
            db.session.rollback()
            raise e
        
    def update_category(self, category_id, name=None, description=None):
        """Обновление категории"""
        try:
            category = Category.query.get(category_id)
            if not category:
                return False
                
            if name is not None:
                category.name = name
            if description is not None:
                category.description = description
                
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    def delete_category(self, category_id):
        """Удаление категории"""
        try:
            category = Category.query.get(category_id)
            if category:
                db.session.delete(category)
                db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    def get_categories(self):
        """Получение списка категорий"""
        categories = Category.query\
            .join(User, Category.user_id == User.id)\
            .add_columns(User.username)\
            .order_by(Category.name)\
            .all()
        
        result = []
        for category, username in categories:
            result.append([
                category.id,
                category.user_id,
                category.name,
                category.description,
                category.created_at,
                username
                ]
            )
        return result
    
    def get_category(self, category_id):
        """Получение категории по ID"""
        category = Category.query\
            .join(User, Category.user_id == User.id)\
            .add_columns(User.username)\
            .filter(Category.id == category_id)\
            .first()
        
        if category:
            cat, username = category
            return [
                cat.id,
                cat.user_id,
                cat.name,
                cat.description,
                cat.created_at,
                username
            ]
        return None

    def create_topic(self, title, content, user_id, category_id):
        """Создание новой темы"""
        try:
            topic = Topic(
                title=title,
                content=content,
                user_id=user_id,
                category_id=category_id
            )
            db.session.add(topic)
            db.session.commit()
            return topic.id
        except Exception as e:
            db.session.rollback()
            raise e
        
    def update_topic(self, topic_id, title=None, content=None):
        """Обновление темы"""
        try:
            topic = Topic.query.get(topic_id)
            if not topic:
                return False
                
            if title is not None:
                topic.title = title
            if content is not None:
                topic.content = content
                
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    def delete_topic(self, topic_id):
        """Удаление темы"""
        try:
            topic = Topic.query.get(topic_id)
            if topic:
                db.session.delete(topic)
                db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
        
    def get_topic(self, topic_id):
        """Получение темы по ID"""
        topic = Topic.query\
            .join(User, Topic.user_id == User.id)\
            .join(Category, Topic.category_id == Category.id)\
            .add_columns(User.username, Category.name)\
            .filter(Topic.id == topic_id)\
            .first()
        
        if topic:
            t, username, category_name = topic
            return [
                t.id,
                t.user_id,
                t.category_id,
                t.title,
                t.content,
                t.created_at,
                username,
                category_name
            ]
        return None
    
    def get_topics(self, category_id=None, limit=10):
        """Получение списка тем (всех или по категории)"""
        query = Topic.query\
            .join(User, Topic.user_id == User.id)\
            .join(Category, Topic.category_id == Category.id)\
            .add_columns(User.username, Category.name)
        
        if category_id:
            query = query.filter(Topic.category_id == category_id)
            
        topics = query.order_by(Topic.created_at.desc()).limit(limit).all()
        
        result = []
        for topic, username, category_name in topics:
            result.append([
                topic.id,
                topic.user_id,
                topic.category_id,
                topic.title,
                topic.content,
                topic.created_at,
                username,
                category_name
            ])
        return result

    def get_post(self, post_id):
        """Получение сообщения по ID"""
        post = Post.query\
            .join(User, Post.user_id == User.id)\
            .join(Topic, Post.topic_id == Topic.id)\
            .add_columns(User.username, Topic.title)\
            .filter(Post.id == post_id)\
            .first()
        
        if post:
            p, username, topic_title = post
            return {
                'id': p.id,
                'user_id': p.user_id,
                'topic_id': p.topic_id,
                'content': p.content,
                'created_at': p.created_at,
                'username': username,
                'topic_title': topic_title
            }
        return None

    def add_post(self, content, user_id, topic_id):
        """Добавление сообщения в тему"""
        try:
            post = Post(
                content=content,
                user_id=user_id,
                topic_id=topic_id
            )
            db.session.add(post)
            db.session.commit()
            return post.id
        except Exception as e:
            db.session.rollback()
            raise e
        
    def update_post(self, post_id, content=None):
        """Обновление сообщения"""
        try:
            post = Post.query.get(post_id)
            if not post:
                return False
                
            if content is not None:
                post.content = content
                
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e

    def delete_post(self, post_id):
        """Удаление сообщения"""
        try:
            post = Post.query.get(post_id)
            if post:
                db.session.delete(post)
                db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e

    def register_user(self, username, email, password):
        """Регистрация нового пользователя"""
        try:
            # Проверка существующего пользователя
            existing_user = User.query.filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                return None, "Пользователь с таким именем или email уже существует"
            
            user = User(
                username=username,
                email=email,
                password=password
            )
            db.session.add(user)
            db.session.commit()
            return user.id, "Регистрация успешна"
        except Exception as e:
            db.session.rollback()
            return None, f"Ошибка регистрации: {e}"

    def login_user(self, username=None, email=None, password=None):
        """Вход пользователя"""
        try:
            if username and password:
                user = User.query.filter_by(username=username, password=password).first()
            elif email and password:
                user = User.query.filter_by(email=email, password=password).first()
            else:
                return None
                
            if user:
                return (user.id, user.username, user.email, user.password)
            return None
        except Exception as e:
            return None

    def update_user(self, user_id, username=None, email=None, password=None):
        """Обновление пользователя"""
        try:
            user = User.query.get(user_id)
            if not user:
                return False
                
            if username is not None:
                user.username = username
            if email is not None:
                user.email = email
            if password is not None:
                user.password = password
                
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e

    def delete_user(self, user_id):
        """Удаление пользователя"""
        try:
            user = User.query.get(user_id)
            if user:
                db.session.delete(user)
                db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e

    def get_user_by_username(self, username):
        """Получение пользователя по имени"""
        user = User.query.filter_by(username=username).first()
        if user:
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'password': user.password,
                'admin': user.admin,
                'created_at': user.created_at
            }
        return None

    def get_user_by_id(self, user_id):
        """Получение пользователя по ID"""
        user = User.query.get(user_id)
        if user:
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'password': user.password,
                'admin': user.admin,
                'created_at': user.created_at
            }
        return None
    # Добавь эти методы в класс DataBase

    def get_all_users(self):
        """Получение всех пользователей"""
        users = User.query.all()
        result = []
        for user in users:
            result.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'admin': user.admin,
                'created_at': user.created_at,
                'topics_count': len(user.topics),
                'posts_count': len(user.posts)
            })
        return result

    def get_all_categories_with_stats(self):
        """Получение всех категорий со статистикой"""
        categories = Category.query.all()
        result = []
        for category in categories:
            topics_count = len(category.topics)
            posts_count = sum(len(topic.posts) for topic in category.topics)
            result.append({
                'id': category.id,
                'name': category.name,
                'author': category.author.username,
                'topics_count': topics_count,
                'posts_count': posts_count,
                'created_at': category.created_at
            })
        return result

    def get_all_topics_with_stats(self):
        """Получение всех тем со статистикой"""
        topics = Topic.query.all()
        result = []
        for topic in topics:
            result.append({
                'id': topic.id,
                'title': topic.title,
                'author': topic.author.username,
                'category': topic.category.name,
                'posts_count': len(topic.posts),
                'created_at': topic.created_at
            })
        return result

    def get_recent_posts(self, limit=20):
        """Получение последних сообщений"""
        posts = Post.query.order_by(Post.created_at.desc()).limit(limit).all()
        result = []
        for post in posts:
            result.append({
                'id': post.id,
                'content': post.content[:100] + '...' if len(post.content) > 100 else post.content,
                'author': post.author.username,
                'topic': post.topic.title,
                'created_at': post.created_at
            })
        return result

    def get_forum_stats(self):
        """Получение общей статистики форума"""
        users_count = User.query.count()
        categories_count = Category.query.count()
        topics_count = Topic.query.count()
        posts_count = Post.query.count()
        
        return {
            'users_count': users_count,
            'categories_count': categories_count,
            'topics_count': topics_count,
            'posts_count': posts_count
        }

    def update_user_admin_status(self, user_id, admin_status):
        """Изменение статуса администратора пользователя"""
        try:
            user = User.query.get(user_id)
            if user:
                user.admin = 1 if admin_status else 0
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            raise e

    def delete_user_admin(self, user_id):
        """Удаление пользователя (админская версия)"""
        try:
            user = User.query.get(user_id)
            if user:
                # Каскадное удаление через отношения
                db.session.delete(user)
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            raise e

# Создаем экземпляр базы данных
if __name__ == "__main__":
    from flask import Flask
    app = Flask(__name__)
    
    database = DataBase(app)
    
    # Теперь можно работать с БД в контексте приложения
    with app.app_context():
        
        print(database.get_posts(1))