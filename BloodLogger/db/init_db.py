import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'bloodlogger.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')

def initialize_database():
    with sqlite3.connect(DB_PATH) as conn:
        with open(SCHEMA_PATH, 'r') as f:
            schema = f.read()
        conn.executescript(schema)
    print(f"Database initialized at {DB_PATH}")

if __name__ == "__main__":
    initialize_database()
