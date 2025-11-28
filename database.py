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
    
    # Create messages table
    c.execute('''
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Optional: sample messages
    sample_msgs = [
        (1, 'Welcome to the vulnerable forum!'),
        (2, 'Hello from user1'),
        (3, 'This is a test message')
    ]
    c.executemany("INSERT INTO messages (user_id, content) VALUES (?, ?)", sample_msgs)
    
    conn.commit()
    conn.close()
    print("База vulnfirm.db успешно создана с таблицами users и messages!")

if __name__ == "__main__":
    create_db()