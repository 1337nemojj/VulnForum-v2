# database.py
import sqlite3
import os

DB_NAME = "vulnfirm.db"

def create_db():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Тестовые пользователи
    users = [
        ('admin', 'admin123', 'admin'),
        ('user1', 'pass123', 'user'),
        ('qwer', 'qwer', 'user')
    ]
    
    c.executemany("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", users)
    
    conn.commit()
    conn.close()
    print("База vulnfirm.db успешно создана с колонкой created_at!")

if __name__ == "__main__":
    create_db()