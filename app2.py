from flask import Flask, render_template, request, redirect, url_for, flash, session

from sqlalchemy_bd import DataBase

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
database = DataBase(app)

# ! Изменить нахуй весь дизайн сайта
# * Переделать кнопку, сделать по отдельности создание тем, категориев и отправку сообщений
# ! Сделать кнопку изменения сообщений
# ! Добавить футер в base.html
# ! Сделать админ панель(Выборка в самих html шаблонах)
# ! Сделать страницу "О НАС"
# ? Написать отчет
# ? Чето сделать прикольное на базе тг бота
# ! Прикрутить систему гит с гитхабом
# ? Протестить хостинг на телефон при помощи Термухи

from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему')
            return redirect(url_for('login'))
        
        user = database.get_user_by_id(session['user_id'])
        if not user or user.get('admin') != 1:
            flash('Недостаточно прав для доступа к админ-панели')
            return redirect(url_for('index'))
            
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@admin_required
def admin_panel():
    """Главная страница админ-панели"""
    stats = database.get_forum_stats()
    recent_posts = database.get_recent_posts(limit=10)
    
    return render_template('admin/index.html', 
                         stats=stats, 
                         recent_posts=recent_posts)

@app.route('/admin/users')
@admin_required
def admin_users():
    """Управление пользователями"""
    users = database.get_all_users()
    return render_template('admin/users.html', users=users)

@app.route('/admin/categories')
@admin_required
def admin_categories():
    """Управление категориями"""
    categories = database.get_all_categories_with_stats()
    return render_template('admin/categories.html', categories=categories)

@app.route('/admin/topics')
@admin_required
def admin_topics():
    """Управление темами"""
    topics = database.get_all_topics_with_stats()
    return render_template('admin/topics.html', topics=topics)

@app.route('/admin/posts')
@admin_required
def admin_posts():
    """Управление сообщениями"""
    posts = database.get_recent_posts(limit=50)
    return render_template('admin/posts.html', posts=posts)

# Действия админ-панели
@app.route('/admin/user/<int:user_id>/toggle_admin', methods=['POST'])
@admin_required
def toggle_user_admin(user_id):
    """Изменение статуса администратора"""
    if user_id == session['user_id']:
        flash('Вы не можете изменить свои собственные права администратора')
        return redirect(url_for('admin_users'))
    
    user = database.get_user_by_id(user_id)
    if user:
        new_status = not user.get('admin')
        database.update_user_admin_status(user_id, new_status)
        status_text = "назначен администратором" if new_status else "лишен прав администратора"
        flash(f'Пользователь {user["username"]} {status_text}')
    else:
        flash('Пользователь не найден')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    """Удаление пользователя"""
    if user_id == session['user_id']:
        flash('Вы не можете удалить свой собственный аккаунт')
        return redirect(url_for('admin_users'))
    
    user = database.get_user_by_id(user_id)
    if user:
        database.delete_user_admin(user_id)
        flash(f'Пользователь {user["username"]} удален')
    else:
        flash('Пользователь не найден')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/category/<int:category_id>/delete', methods=['POST'])
@admin_required
def admin_delete_category(category_id):
    """Удаление категории"""
    category = database.get_category(category_id)
    if category:
        database.delete_category(category_id)
        flash(f'Категория {category[2]} удалена')  # category[2] = name
    else:
        flash('Категория не найдена')
    
    return redirect(url_for('admin_categories'))

@app.route('/admin/topic/<int:topic_id>/delete', methods=['POST'])
@admin_required
def admin_delete_topic(topic_id):
    """Удаление темы"""
    topic = database.get_topic(topic_id)
    if topic:
        database.delete_topic(topic_id)
        flash(f'Тема "{topic[3]}" удалена')  # topic[3] = title
    else:
        flash('Тема не найдена')
    
    return redirect(url_for('admin_topics'))

@app.route('/admin/post/<int:post_id>/delete', methods=['POST'])
@admin_required
def admin_delete_post(post_id):
    """Удаление сообщения"""
    post = database.get_post(post_id)
    if post:
        database.delete_post(post_id)
        flash(f'Сообщение #{post_id} удалено')
    else:
        flash('Сообщение не найдено')
    
    return redirect(url_for('admin_posts'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'delete':
            category_id = request.form['category_id']
            
            database.delete_category(category_id)
            flash('Категория удалена')
        else:
            name = request.form['name']
            description = request.form['description']
            user_id = session['user_id']
            database.create_category(name,description, user_id)
            flash('Вы создали категорию')
    categories = database.get_categories()
    recent_topics = database.get_topics()
    return render_template('index.html', categories=categories, recent_topics=recent_topics)
@app.route('/category/<int:category_id>', methods=['GET', 'POST'])
def category(category_id):
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'delete':
            topic_id = request.form['topic_id']
            
            database.delete_topic(topic_id)
            flash('Категория удалена')
        else:
            name = request.form['name']
            description = request.form['description']
            user_id = session['user_id']
            database.create_topic(name,description, user_id, category_id)
            flash('Вы создали тему')
    category = database.get_category(category_id)
    topics = database.get_topics(category_id)
    return render_template('category.html', category=category, topics=topics)

@app.route('/topic/<int:topic_id>', methods=['GET', 'POST'])
def topic(topic_id):
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'delete':
            post_id = request.form['post_id']
            database.delete_post(post_id)
            flash('Категория удалена')
        else:
            content = request.form['content']
            user_id = session['user_id']
            database.add_post(content, user_id, topic_id)
            flash('Вы отправили сообщение')
    topic = database.get_topic(topic_id)
    posts = database.get_posts(topic_id)
    return render_template('topic.html', topic=topic, posts=posts, category=topic[2])

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы')
    return redirect(url_for('index'))
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = database.login_user(username=username,email=username, password=password)
        
        if user is not None:
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('Вы успешно вошли в систему!')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль')
    # * Доделать вход login.html
    # session['username'] = 'username'
    # flash('Вы вошли в систему')
    return render_template('login.html')
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        user = database.register_user(username,email,password)
        
        if user[0] is not None:
            user_log = database.login_user(username=username,email=email, password=password)
            session['user_id'] = user_log[0]
            session['username'] = user_log[1]
            flash('Вы успешно зарегистрировались в систему!')
            return redirect(url_for('index'))
        else:
            flash(f'{user[1]}')
    # * Доделать регистрацию login.html
    # session['username'] = 'username'
    # flash('Вы зарегистрировались в систему')
    return render_template('register.html')
with app.app_context():
        user = database.get_user_by_username('Faf')
        if user:
            database.update_user_admin_status(user['id'], True)
            print(f"Пользователь {user['username']} теперь админ")


if __name__ == '__main__':
    app.run(debug=True)
    # Временный скрипт для назначения админа
    