from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from database import init_db, get_db_connection
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Измените на случайный ключ

# Инициализация базы данных
init_db()

@app.route('/')
def index():
    conn = get_db_connection()
    
    # Получаем категории и количество тем в каждой
    categories = conn.execute('''
        SELECT c.*, COUNT(t.id) as topic_count 
        FROM categories c 
        LEFT JOIN topics t ON c.id = t.category_id 
        GROUP BY c.id
    ''').fetchall()
    
    # Последние темы
    recent_topics = conn.execute('''
        SELECT t.*, u.username, c.name as category_name 
        FROM topics t 
        JOIN users u ON t.user_id = u.id 
        JOIN categories c ON t.category_id = c.id 
        ORDER BY t.created_at DESC 
        LIMIT 10
    ''').fetchall()
    
    conn.close()
    return render_template('index.html', categories=categories, recent_topics=recent_topics)

@app.route('/category/<int:category_id>')
def category(category_id):
    conn = get_db_connection()
    
    category = conn.execute('SELECT * FROM categories WHERE id = ?', (category_id,)).fetchone()
    topics = conn.execute('''
        SELECT t.*, u.username, COUNT(p.id) as post_count 
        FROM topics t 
        JOIN users u ON t.user_id = u.id 
        LEFT JOIN posts p ON t.id = p.topic_id 
        WHERE t.category_id = ? 
        GROUP BY t.id 
        ORDER BY t.created_at DESC
    ''', (category_id,)).fetchall()
    
    conn.close()
    return render_template('category.html', category=category, topics=topics)

@app.route('/topic/<int:topic_id>')
def topic(topic_id):
    conn = get_db_connection()
    
    topic = conn.execute('''
        SELECT t.*, u.username as author, c.name as category_name 
        FROM topics t 
        JOIN users u ON t.user_id = u.id 
        JOIN categories c ON t.category_id = c.id 
        WHERE t.id = ?
    ''', (topic_id,)).fetchone()
    
    posts = conn.execute('''
        SELECT p.*, u.username 
        FROM posts p 
        JOIN users u ON p.user_id = u.id 
        WHERE p.topic_id = ? 
        ORDER BY p.created_at ASC
    ''', (topic_id,)).fetchall()
    
    conn.close()
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
        user_id = session['user_id']
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO topics (title, content, category_id, user_id) 
            VALUES (?, ?, ?, ?)
        ''', (title, content, category_id, user_id))
        conn.commit()
        conn.close()
        
        flash('Тема успешно создана!')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    categories = conn.execute('SELECT * FROM categories').fetchall()
    conn.close()
    
    return render_template('create_topic.html', categories=categories)

@app.route('/create_post/<int:topic_id>', methods=['POST'])
def create_post(topic_id):
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему чтобы оставить сообщение')
        return redirect(url_for('login'))
    
    content = request.form['content']
    user_id = session['user_id']
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO posts (content, topic_id, user_id) 
        VALUES (?, ?, ?)
    ''', (content, topic_id, user_id))
    conn.commit()
    conn.close()
    
    flash('Сообщение успешно добавлено!')
    return redirect(url_for('topic', topic_id=topic_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password_confirm = request.form['password_confirm']
        
        if password != password_confirm:
            flash('Пароли не совпадают')
            return render_template('register.html')
        
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO users (username, email, password) 
                VALUES (?, ?, ?)
            ''', (username, email, hashed_password))
            conn.commit()
            flash('Регистрация успешна! Теперь вы можете войти.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Пользователь с таким именем или email уже существует')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
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

if __name__ == '__main__':
    app.run(debug=True)