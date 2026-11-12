import sqlite3

DB_NAME = "booking.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'patient'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            fee INTEGER NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'booked',
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        )
    """)

    
    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS unique_slot
        ON appointments(doctor_id, date, time)
        WHERE status = 'booked'
    """)

    
    count = cur.execute("SELECT COUNT(*) FROM doctors").fetchone()[0]
    if count == 0:
        cur.executemany(
            "INSERT INTO doctors (name, specialization, fee) VALUES (?, ?, ?)",
            [
                ("Dr. Sharma", "Cardiologist", 800),
                ("Dr. Verma", "Dermatologist", 600),
                ("Dr. Khan", "General Physician", 400),
            ],
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database ban gaya!")
