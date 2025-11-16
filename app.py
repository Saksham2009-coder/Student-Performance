import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_bcrypt import Bcrypt   # correct bcrypt import

app = Flask(__name__)

# Secret key
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey123")

# bcrypt instance
bcrypt = Bcrypt(app)

# Rate limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per hour"]
)

# ---------------------------
# DATABASE SETUP
# ---------------------------

DB = "students.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            physics INTEGER,
            chemistry INTEGER,
            math INTEGER,
            cs INTEGER,
            english INTEGER,
            total INTEGER,
            percentage REAL,
            cgpa REAL,
            grade TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------------------
# LOGIN SYSTEM
# ---------------------------

ADMIN_USERNAME = "Saksham"

# bcrypt hash for password "8700986782"
ADMIN_PASSWORD_HASH = b"$2b$12$9Hys6p7eJxLdIH8YjNXn8uOeN8zQ3cZlSA.9bNyUmDAgbxzIc/cgq"


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "admin" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"].encode()

        # password check
        if username == ADMIN_USERNAME and bcrypt.check_password_hash(ADMIN_PASSWORD_HASH, password):
            session["admin"] = True
            return redirect(url_for("home"))

        return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------------------
# STUDENT SYSTEM
# ---------------------------

def calculate_results(p, c, m, cs, e):
    total = p + c + m + cs + e
    percentage = (total / 500) * 100
    cgpa = min(round(total / 50, 2), 10)

    if percentage >= 90:
        grade = "A+"
    elif percentage >= 80:
        grade = "A"
    elif percentage >= 70:
        grade = "B"
    elif percentage >= 60:
        grade = "C"
    elif percentage >= 50:
        grade = "D"
    else:
        grade = "F"

    return total, percentage, cgpa, grade


@app.route("/")
@login_required
def home():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    students = c.execute("SELECT * FROM students ORDER BY percentage DESC").fetchall()
    conn.close()

    return render_template("index.html", students=students)


@app.route("/add", methods=["POST"])
@login_required
def add_student():
    name = request.form.get("name").strip()
    marks = [int(request.form.get(s) or 0) for s in ["physics", "chemistry", "math", "cs", "english"]]

    for mark in marks:
        if mark < 0 or mark > 100:
            return "<h3>Error: Marks must be between 0–100</h3><a href='/'>Go Back</a>"

    p, c, m, cs, e = marks
    total, percentage, cgpa, grade = calculate_results(p, c, m, cs, e)

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        INSERT INTO students (name, physics, chemistry, math, cs, english, total, percentage, cgpa, grade)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, p, c, m, cs, e, total, percentage, cgpa, grade))

    conn.commit()
    conn.close()

    return redirect(url_for("home"))


@app.route("/clear", methods=["POST"])
@login_required
def clear_all():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    top = c.execute("SELECT * FROM students ORDER BY percentage DESC LIMIT 1").fetchone()

    c.execute("DELETE FROM students")

    if top:
        c.execute("""
            INSERT INTO students (name, physics, chemistry, math, cs, english, total, percentage, cgpa, grade)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, top[1:])

    conn.commit()
    conn.close()

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
