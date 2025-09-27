import sqlite3
import os

print('Checking database...')
db_path = 'db_memoria/metadata.sqlite'
print(f'Database exists: {os.path.exists(db_path)}')

if os.path.exists('db_memoria'):
    print(f'Directory contents: {os.listdir("db_memoria")}')
else:
    print('Directory does not exist')

# Try to connect to database
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f'Tables in database: {tables}')

    if tables:
        cursor.execute("SELECT COUNT(*) FROM papers")
        count = cursor.fetchone()[0]
        print(f'Number of papers in database: {count}')

    conn.close()
except Exception as e:
    print(f'Error accessing database: {e}')
