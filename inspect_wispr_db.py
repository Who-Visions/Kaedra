import sqlite3
import os

db_path = r"C:\Users\super\AppData\Roaming\Wispr Flow\flow.sqlite"

try:
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print("Tables found:")
    for table in tables:
        table_name = table[0]
        print(f"- {table_name}")
        
        # Get schema for each table
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")

    conn.close()

except Exception as e:
    print(f"An error occurred: {e}")
