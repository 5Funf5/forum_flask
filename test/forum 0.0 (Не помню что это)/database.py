import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('forum.db')
    c = conn.cursor()
    
    # Таблица пользователей
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица разделов
    c.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        )
    ''')
    
    # Таблица тем
    c.execute('''
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category_id INTEGER,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Таблица сообщений
    c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            topic_id INTEGER,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (topic_id) REFERENCES topics (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Добавляем тестовые категории
    categories = [
        ('Общие обсуждения', 'Обсуждения на разные темы'),
        ('Технические вопросы', 'Помощь с техническими проблемами'),
        ('Предложения', 'Предложения по улучшению форума')
    ]
    
    c.executemany('INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)', categories)
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('forum.db')
    conn.row_factory = sqlite3.Row
    return conn