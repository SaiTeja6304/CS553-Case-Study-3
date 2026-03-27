import sqlite3

def create_connection():
    conn = sqlite3.connect('chat_vlm.db')
    cursor = conn.cursor()
    return conn, cursor

def create_table(conn, cursor):
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_vlm_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        local_model TEXT NOT NULL,
        query TEXT NOT NULL,
        response TEXT NOT NULL,
        chat_history TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()

def insert_log(conn, cursor, local_model, query, response, chat_history):
    cursor.execute('''
    INSERT INTO chat_vlm_logs (local_model, query, response, chat_history)
    VALUES (?, ?, ?, ?)
    ''', (local_model, query, response, chat_history))
    conn.commit()

def close_connection(conn, cursor):
    cursor.close()
    conn.close()
