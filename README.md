# Doctor Appointment Booking System

A simple web app built with **Flask** and **SQLite** where patients can book appointments with doctors, and an admin can manage doctors and view all bookings.

## Features
- Register and login (passwords are hashed)
- View doctors and book an appointment (date + time slot)
- Double-booking is prevented (one doctor, one slot, one patient)
- View and cancel your own appointments
- Admin panel: view all appointments, add new doctors

## Tech stack
- Python, Flask
- SQLite
- HTML, CSS (Jinja2 templates)

## Run locally
```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

The database (`booking.db`) is created automatically on first run, with 3 sample doctors.

## Make a user admin
Register a normal account first, then run:
```bash
python make_admin.py
```
Enter that account's email, then log out and log in again.

## Project structure
```
app.py            main Flask app (routes)
database.py       database setup and tables
make_admin.py     script to promote a user to admin
templates/        HTML pages
static/style.css  styling
```
