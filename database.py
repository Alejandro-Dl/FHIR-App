# database.py
import sqlite3
import os

DB_PATH  = os.path.join(os.path.dirname(__file__), "data", "clinic.db")
SQL_PATH = os.path.join(os.path.dirname(__file__), "FHIR.sql")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create tables from your exported SQL file if they don't exist yet."""
    conn = get_connection()
    with open(SQL_PATH, "r") as f:
        sql = f.read()
    conn.executescript(sql)
    conn.commit()
    conn.close()
    print("[database] DB initialised from SQL file.")

