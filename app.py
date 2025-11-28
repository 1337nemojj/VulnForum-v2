from flask import Flask, request, render_template, session, redirect, url_for, abort, flash
import sqlite3
from datetime import datetime
import os
import requests  # A10: SSRF
import subprocess


app = Flask(__name__)
app.secret_key = 'super_secret_key'  # A05: Security Misconfiguration (слабый секрет)
app.debug = True  # A05: Debug mode включён (утечка info)

# A09: No logging (ничего не логируем)

def get_db():
    conn = sqlite3.connect('vulnfirm.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('forum'))
    return redirect(url_for('login'))

@app.route('/ping', methods=['GET', 'POST'])
def ping_host():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    result = ""
    if request.method == 'POST':
        host = request.form.get('host', '')
        if host:
            # OS Command Injection
            try:
                # Используем subprocess с shell=True + прямой конкатенацией
                cmd = f"ping -n 4 {host}"  # -n 4 для Windows, -c 4 будет на Linux
                output = subprocess.check_output(cmd, shell=True, text=True, timeout=15)
                result = f"<pre>{output}</pre>"
            except Exception as e:
                result = f"<pre style='color:#ff5555;'>Ошибка: {e}</pre>"
    
    return render_template('ping.html', result=result)
@app.route('/register', methods=['GET', 'POST'])

def register():
    # A07: No validation, passwords in plaintext
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']  
        conn = get_db()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("User exists!")
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # A03: SQL Injection в логине
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        c = conn.cursor()
        # Vulnerable: 
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        c.execute(query)
        user = c.fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('forum'))
        flash("Invalid credentials!")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))



@app.route('/forum', methods=['GET', 'POST'])
def forum():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    if request.method == 'POST':
        content = request.form['content']  # A03/A01: Stored XSS, no escaping
        c.execute("INSERT INTO messages (user_id, content) VALUES (?, ?)", (session['user_id'], content))
        conn.commit()
    c.execute("SELECT m.*, u.username FROM messages m JOIN users u ON m.user_id = u.id ORDER BY m.timestamp DESC")
    messages = c.fetchall()
    conn.close()
    return render_template('forum.html', messages=messages)

@app.route('/profile/<username>')
def profile(username):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute(f"SELECT id, username, password, role, created_at FROM users WHERE username = '{username}'")
        user = c.fetchone()
    except:
        user = None
    
    conn.close()
    
    if not user:
        return "<h2>Пользователь не найден</h2>", 404
        
    return render_template('profile.html', user=user)

@app.route('/search')
def search():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    query = request.args.get('q', '').strip()
    users = []

    if query:
        conn = get_db()
        c = conn.cursor()
        
        # ← ВОТ ОНА — НАСТОЯЩАЯ, СКРЫТАЯ SQL INJECTION!
        sql = f"SELECT username, role, created_at FROM users WHERE username LIKE '%{query}%'"
        try:
            c.execute(sql)
            rows = c.fetchall()
            for row in rows:
                users.append({
                    'username': row[0],
                    'role': row[1] or 'user',
                    'registered_at': row[2] or '—'
                })
        except Exception as e:
            # При ошибке — просто пусто (не падаем)
            pass
        conn.close()

    return render_template('search.html', users=users, query=query)

@app.route('/admin')
def admin():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') != 'admin':
        return "<h1 style='color:#ff5555;'>Доступ запрещён. Требуется роль admin.</h1>", 403
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()
    return render_template('admin.html', users=users)

@app.route('/ssrf', methods=['GET', 'POST'])
def ssrf_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    result = ""
    if request.method == 'POST':
        url = request.form.get('url', '')
        try:
            response = requests.get(url, timeout=5)
            result = response.text[:2000]
        except Exception as e:
            result = f"Ошибка: {str(e)}"
    
    return render_template('ssrf.html', result=result)

@app.route('/internal-admin')
def internal_admin():
    # Доступ только с localhost (127.0.0.1 или ::1)
    if request.remote_addr not in ['127.0.0.1', '::1']:
        abort(403)
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()
    
    return render_template('admin.html', users=users)
@app.route('/update_profile/<int:user_id>', methods=['POST'])
def update_profile(user_id):
    # A04: Insecure Design — предсказуемые ID, no auth check
    # A08: No integrity check (e.g., no hash verification)
    new_role = request.form['role']
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET role=? ", (new_role,))
    conn.commit()
    conn.close()
    return "Updated!"

# On startup: ensure the database and required tables exist. This makes local setup easier
try:
    import database
except Exception:
    database = None

DB_PATH = 'vulnfirm.db'
if database and not os.path.exists(DB_PATH):
    # Create the full DB (users + messages)
    database.create_db()
else:
    # If DB exists, ensure messages table exists (older DBs may lack it)
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute("SELECT 1 FROM messages LIMIT 1")
        except sqlite3.OperationalError:
            c.execute('''
                CREATE TABLE messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')
            conn.commit()
        finally:
            conn.close()
    except Exception:
        # If anything goes wrong here, we don't want to crash the server startup.
        pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, ssl_context=None)  # A02: No HTTPS