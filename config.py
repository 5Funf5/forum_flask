class CONFIG:
    db = 'forum.db'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{db}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'your-secret-key-here'
