import sqlite3

DB_PATH = r"C:\Users\super\AppData\Roaming\Wispr Flow\flow.sqlite"

try:
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    cursor = conn.cursor()
    
    print("--- COUNT ---")
    cursor.execute("SELECT COUNT(*) FROM History")
    print(cursor.fetchone()[0])

    print("\n--- LAST 5 ENTRIES (by timestamp) ---")
    query = """
    SELECT asrText, formattedText, timestamp, status 
    FROM History 
    ORDER BY timestamp DESC 
    LIMIT 5
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    for i, row in enumerate(rows):
        print(f"[{i}] Timestamp: {row[2]}")
        print(f"    ASR: {row[0]}")
        print(f"    Formatted: {row[1]}")
        print(f"    Status: {row[3]}")
        print("-" * 20)
        
    conn.close()

except Exception as e:
    print(f"Error: {e}")
