import sqlite3
import hashlib

DB_NAME = "finance.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    #Income table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS income (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    
    #users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
    )
    """)

    #expense table
    #(foreign key relationship)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    category TEXT NOT NULL,
    amount REAL NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)



    conn.commit()
    conn.close()

def add_expense(user_id, category, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO expenses (user_id, category, amount) VALUES (?, ?, ?)",
        (user_id, category, amount)
    )
    

    conn.commit()
    conn.close()

def get_expenses(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT category, amount FROM expenses WHERE user_id = ?",
        (user_id,)
    )
    rows = cursor.fetchall()

    conn.close()

    return rows

def delete_all_expenses():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM expenses")

    conn.commit()
    conn.close()

def save_income(user_id,amount):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM income WHERE user_id = ?", (user_id,))
    cursor.execute(
        "INSERT INTO income (user_id, amount) VALUES (?, ?)",
        (user_id, amount)
    )

    conn.commit()
    conn.close()

def get_income(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT amount FROM income WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()

    conn.close()

    return row[0] if row else 0

def hash_password(password):  #converts password into encrypted form
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    conn=get_connection()
    cursor=conn.cursor()
    hashed=hash_password(password)

    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?,?)", 
                       (username,hashed))
        conn.commit()
        return True
    except:
        return False
    finally: 
        conn.close()

def login_user(username,password):
    conn=get_connection()
    cursor=conn.cursor()
    hashed=hash_password(password)

    cursor.execute("SELECT id FROM users WHERE username= ? AND password=?", 
                   (username,hashed))
    user=cursor.fetchone()
    conn.close()

    return user[0] if user else None

def update_category(user_id, old_category, amount, new_category):
    conn=get_connection()
    cursor=conn.cursor()

    cursor.execute(
        """ 
        UPDATE expenses
        SET category = ?
        WHERE user_id = ? AND category = ? AND amount = ?
        """,
        (new_category, user_id, old_category, amount)
    )
    conn.commit()
    conn.close()
