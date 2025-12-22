from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

DB_URL = 'sqlite:///database.db'
engine = create_engine(
    DB_URL, 
    echo=True,)

with engine.connect() as conn:
    res = conn.execute(text('SELECT sqlite_version()'))
    print(f'{res.first()=}')