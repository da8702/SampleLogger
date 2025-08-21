import sqlite3
import os

TEMPLATE_DB = os.path.join(os.path.dirname(__file__), '../ui/db/bloodlogger_template.db')
SCHEMA = os.path.join(os.path.dirname(__file__), 'schema.sql')

def create_template_db():
    os.makedirs(os.path.dirname(TEMPLATE_DB), exist_ok=True)
    conn = sqlite3.connect(TEMPLATE_DB)
    with open(SCHEMA, 'r') as f:
        conn.executescript(f.read())
    conn.close()
    print(f"Template DB created at: {TEMPLATE_DB}")

if __name__ == '__main__':
    create_template_db()
