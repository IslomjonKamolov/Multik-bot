import sqlite3

conn = sqlite3.connect("codes.db")
cursor = conn.cursor()

def create_table():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        url TEXT
    )
    """)
    conn.commit()

# Yangi kod qo'shish
def add_code(code, url):
    cursor.execute("INSERT INTO codes (code, url) VALUES (?, ?)", (code, url))
    conn.commit()

# Kod bo'yicha URL olish
def get_url_by_code(code):
    cursor.execute("SELECT url FROM codes WHERE code = ?", (code,))
    result = cursor.fetchone()
    return result[0] if result else None

# Kod mavjudligini tekshirish
def check_code_exists(code):
    cursor.execute("SELECT 1 FROM codes WHERE code = ?", (code,))
    return cursor.fetchone() is not None

create_table()
