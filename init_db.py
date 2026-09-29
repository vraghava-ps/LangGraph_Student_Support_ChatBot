import sqlite3
from config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS payments")
cur.execute("""
CREATE TABLE payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    course TEXT NOT NULL,
    amount INTEGER NOT NULL,
    status TEXT NOT NULL,          -- PAID / PENDING / FAILED
    due_date TEXT,
    paid_on TEXT
)
""")

rows = [
    ("STU1001", "Python Programming (Beginner to Advanced)", 15000, "PAID", "2026-08-01", "2026-07-28"),
    ("STU1001", "DevOps with AWS", 45000, "PENDING", "2026-10-15", None),
    ("STU1002", "Generative AI (GenAI)", 35000, "FAILED", "2026-09-20", None),
    ("STU1003", "Agentic AI with LangGraph", 30000, "PAID", "2026-09-01", "2026-08-30"),
    ("STU1004", "DevOps with Azure", 45000, "PENDING", "2026-10-05", None),
]
cur.executemany(
    "INSERT INTO payments (student_id, course, amount, status, due_date, paid_on) VALUES (?, ?, ?, ?, ?, ?)",
    rows,
)

conn.commit()
conn.close()
print("Database initialised with sample payment data.")