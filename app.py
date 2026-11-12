import sqlite3
from datetime import date
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, init_db

app = Flask(__name__)
app.secret_key = "koi-bhi-lamba-sercet-text-yahan-likho"

init_db()
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Pehle login karo.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Ye page sirf admin ke liye hai.")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return wrapper


TIME_SLOTS = ["10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "17:00"]


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not name or not email or len(password) < 6:
            flash("sab fields nharo. passowrd kam se kam 6 character ka ho")
            return redirect(url_for("register"))

        hashed = generate_password_hash(password)

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, hashed),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            flash("ye email pehle se registered hai.")
            return redirect(url_for("register"))
        finally:
            conn.close()

        flash("Registration ho gaya! Ab login karo.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            flash(f"Welcome, {user['name']}!")

            return redirect(url_for("home"))

        flash("Email ya password galat hai.")
        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logout ho gaya.")
    return redirect(url_for("home"))


@app.route("/doctors")
@login_required
def doctors():
    conn = get_db()
    doctor_list = conn.execute("SELECT * FROM doctors").fetchall()
    conn.close()
    return render_template("doctors.html", doctors=doctor_list)


@app.route("/book/<int:doctor_id>", methods=["GET", "POST"])
@login_required
def book(doctor_id):
    conn = get_db()
    doctor = conn.execute(
        "SELECT * FROM doctors WHERE id = ?", (doctor_id,)
    ).fetchone()

    if doctor is None:
        conn.close()
        flash("Doctor nahi mila.")
        return redirect(url_for("doctors"))

    if request.method == "POST":
        appt_date = request.form["date"]
        appt_time = request.form["time"]

        try:
            chosen = date.fromisoformat(appt_date)
        except ValueError:
            chosen = None

        if chosen is None or chosen < date.today() or appt_time not in TIME_SLOTS:
            conn.close()
            flash("Sahi date aur time chuno. Purani date nahi chalegi.")
            return redirect(url_for("book", doctor_id=doctor_id))

        try:
            conn.execute(
                "INSERT INTO appointments (user_id, doctor_id, date, time) "
                "VALUES (?, ?, ?, ?)",
                (session["user_id"], doctor_id, appt_date, appt_time),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            flash("Ye slot pehle se book hai. Koi aur time chuno.")
            return redirect(url_for("book", doctor_id=doctor_id))
        finally:
            conn.close()

        flash(f"Appointment book ho gayi: {doctor['name']}, {appt_date} {appt_time}")
        return redirect(url_for("my_appointments"))

    conn.close()
    return render_template(
        "book.html",
        doctor=doctor,
        slots=TIME_SLOTS,
        today=date.today().isoformat(),
    )

@app.route("/my-appointments")
@login_required
def my_appointments():
    conn = get_db()

    rows = conn.execute(
        """
        SELECT a.id, a.date, a.time, a.status,
               d.name AS doctor_name, d.specialization, d.fee
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.user_id = ?
        ORDER BY a.date, a.time
        """,
        (session["user_id"],),
    ).fetchall()
    conn.close()
    return render_template("my_appointments.html", appointments=rows)


@app.route("/cancel/<int:appointment_id>", methods=["POST"])
@login_required
def cancel(appointment_id):
    conn = get_db()
    cur = conn.execute(
        "UPDATE appointments SET status = 'cancelled' "
        "WHERE id = ? AND user_id = ? AND status = 'booked'",
        (appointment_id, session["user_id"]),
    )
    conn.commit()
    changed = cur.rowcount
    conn.close()

    if changed:
        flash("Appointment cancel ho gayi.")
    else:
        flash("Ye appointment cancel nahi ho sakti.")
    return redirect(url_for("my_appointments"))

@app.route("/admin")
@login_required
@admin_required
def admin():
    conn = get_db()
    rows = conn.execute(
        """
        SELECT a.id, a.date, a.time, a.status,
               u.name AS patient_name, u.email AS patient_email,
               d.name AS doctor_name
        FROM appointments a
        JOIN users u ON a.user_id = u.id
        JOIN doctors d ON a.doctor_id = d.id
        ORDER BY a.date, a.time
        """
    ).fetchall()
    conn.close()
    return render_template("admin.html", appointments=rows)


@app.route("/admin/add-doctor", methods=["GET", "POST"])
@login_required
@admin_required
def add_doctor():
    if request.method == "POST":
        name = request.form["name"].strip()
        specialization = request.form["specialization"].strip()

        try:
            fee = int(request.form["fee"])
        except ValueError:
            fee = None

        if not name or not specialization or fee is None or fee <= 0:
            flash("Sab fields sahi bharo. Fee positive number honi chahiye.")
            return redirect(url_for("add_doctor"))

        conn = get_db()
        conn.execute(
            "INSERT INTO doctors (name, specialization, fee) VALUES (?, ?, ?)",
            (name, specialization, fee),
        )
        conn.commit()
        conn.close()

        flash(f"{name} add ho gaye.")
        return redirect(url_for("admin"))

    return render_template("add_doctor.html")



if __name__ == "__main__":
    app.run(debug=True)

