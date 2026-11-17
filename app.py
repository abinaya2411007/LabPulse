
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = "labpulse_development_secret_key"


# DATABASE CONNECTION
def get_db():
    conn = sqlite3.connect("labpulse.db")
    conn.row_factory = sqlite3.Row
    return conn


# CREATE DATABASE
def create_database():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id TEXT UNIQUE,
            name TEXT,
            location TEXT,
            status TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_no TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.executemany("""
        INSERT OR IGNORE INTO equipment
        (equipment_id, name, location, status)
        VALUES (?, ?, ?, ?)
    """, [
        ("EQ001", "Computer", "Computer Lab 1", "Available"),
        ("EQ002", "Oscilloscope", "Electronics Lab", "In Use"),
        ("EQ003", "Projector", "Computer Lab 2", "Available"),
        ("EQ004", "Printer", "IT Lab", "In Use")
    ])

    conn.commit()
    conn.close()


create_database()


# HOME DASHBOARD
@app.route("/")
def home():
    return render_template("dashboard.html")


# STUDENT REGISTRATION
@app.route("/student-register", methods=["GET", "POST"])
def student_register():

    if request.method == "POST":

        name = request.form["name"].strip()
        roll_no = request.form["roll_no"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]

        if not name or not roll_no or not email or not password:
            flash("Please fill all fields.")
            return redirect(url_for("student_register"))

        if len(password) < 8:
            flash("Password must contain at least 8 characters.")
            return redirect(url_for("student_register"))

        hashed_password = generate_password_hash(password)

        conn = get_db()

        try:
            conn.execute("""
                INSERT INTO students
                (name, roll_no, email, password)
                VALUES (?, ?, ?, ?)
            """, (name, roll_no, email, hashed_password))

            conn.commit()
            flash("Registration successful! Please login.")

            return redirect(url_for("student_login"))

        except sqlite3.IntegrityError:
            flash("Roll number or email already exists.")

        finally:
            conn.close()

    return render_template("student_register.html")


# STUDENT LOGIN
@app.route("/student-login", methods=["GET", "POST"])
def student_login():

    if request.method == "POST":

        login_id = request.form["login_id"].strip()
        password = request.form["password"]

        conn = get_db()

        student = conn.execute("""
            SELECT * FROM students
            WHERE roll_no = ? OR email = ?
        """, (login_id, login_id)).fetchone()

        conn.close()

        if student and check_password_hash(
            student["password"], password
        ):

            session["student_id"] = student["id"]
            session["student_name"] = student["name"]

            return redirect(url_for("student_portal"))

        else:
            flash("Invalid Roll Number/Email or Password.")

    return render_template("student_login.html")


# STUDENT DASHBOARD
@app.route("/student-portal")
def student_portal():

    if "student_id" not in session:
        return redirect(url_for("student_login"))

    conn = get_db()

    student = conn.execute("""
        SELECT * FROM students
        WHERE id = ?
    """, (session["student_id"],)).fetchone()

    equipment = conn.execute("""
        SELECT * FROM equipment
    """).fetchall()

    available = conn.execute("""
        SELECT COUNT(*) FROM equipment
        WHERE status = 'Available'
    """).fetchone()[0]

    conn.close()

    return render_template(
        "student_portal.html",
        student=student,
        equipment=equipment,
        available=available
    )


# STUDENT LOGOUT
@app.route("/student-logout")
def student_logout():

    session.clear()

    flash("You have logged out successfully.")

    return redirect(url_for("student_login"))


if __name__ == "__main__":
    app.run(debug=True)
