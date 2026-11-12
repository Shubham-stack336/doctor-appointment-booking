import sqlite3

email = input("Admin banana hai us user ka eamil:").strip().lower()

conn = sqlite3.connect("booking.db")
cur = conn.execute("UPDATE users SET role = 'admin' WHERE email = ?", (email,))
conn.commit()

print("Ho gaya!" if cur.rowcount else "ye email nahi mila")
conn.close()