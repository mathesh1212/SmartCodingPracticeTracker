from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)

app.secret_key="smartcodingtracker123"

conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fullname TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS practice (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    language TEXT NOT NULL,
    topic TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    duration INTEGER NOT NULL,
    status TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    
    if request.method == "POST":
        
        username = request.form["username"]
        password = request.form["password"]
        
        sql = "SELECT * FROM users WHERE username=?"
        
        cursor.execute(sql, (username,))
        
        user = cursor.fetchone()
        
        if user:
            if check_password_hash(user[4], password):
                
                session["username"] = user[3]
                session["fullname"] = user[1]
                return redirect("/dashboard")
            else:
                return "Invalid Password"
            
        return "User Not Found"
        
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():

    if "username" not in session:
        return redirect("/login")

    username = session["username"]

    # Total Topics
    cursor.execute(
    "SELECT COUNT(*) FROM practice WHERE username=?",
    (username,)
    )

    total_topics = cursor.fetchone()[0]

    # Total Practice Time
    cursor.execute(
    "SELECT IFNULL(SUM(duration),0) FROM practice WHERE username=?",
    (username,)
    )
    total_time = cursor.fetchone()[0]

    # Completed Count
    cursor.execute(
    "SELECT COUNT(*) FROM practice WHERE username=? AND status='Completed'",
    (username,)
    )
    completed = cursor.fetchone()[0]

    # Pending Count
    cursor.execute(
    "SELECT COUNT(*) FROM practice WHERE username=? AND status='Pending'",
    (username,)
    )
    pending = cursor.fetchone()[0]
    
    if total_topics > 0:
        progress = int((completed / total_topics) * 100)
    else:
        progress = 0
    
    # Recent Practice History
    cursor.execute("""
    SELECT id, language, topic, difficulty,
    duration, status, created_at
    FROM practice
    WHERE username=?
    ORDER BY id DESC
    """, (username,))

    practice_list = cursor.fetchall()
    
    cursor.execute("""
    SELECT language, topic, status
    FROM practice
    WHERE username=?
    ORDER BY id DESC
    LIMIT 5
    """, (username,))

    recent_activity = cursor.fetchall()
    
    cursor.execute("""
    SELECT language, COUNT(*)
    FROM practice
    WHERE username=?
    GROUP BY language
    """, (username,))
    
    language_data = cursor.fetchall()
    
    labels = []
    values = []

    for row in language_data:
        labels.append(row[0])
        values.append(row[1])

    return render_template(
        "dashboard.html",
        fullname=session["fullname"],
        total_topics=total_topics,
        total_time=total_time,
        completed=completed,
        pending=pending,
        practice_list=practice_list,
        progress=progress,
        recent_activity=recent_activity,
        labels=labels,
        values=values
    )
    
@app.route("/view_practice/<int:id>")
def view_practice(id):

    if "username" not in session:
        return redirect("/login")

    cursor.execute("""
        SELECT language,
               topic,
               difficulty,
               duration,
               status,
               notes,
               created_at
        FROM practice
        WHERE id=?
        AND username=?
    """, (id, session["username"]))

    practice = cursor.fetchone()

    if practice is None:
        return "Practice record not found", 404

    return render_template(
        "view_practice.html",
        practice=practice
    )
    
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/delete/<int:id>")
def delete(id):

    if "username" not in session:
        return redirect("/login")

    sql = """
    DELETE FROM practice
    WHERE id=%s AND username=%s
    """

    cursor.execute(sql, (id, session["username"]))
    conn.commit()

    return redirect("/dashboard")

@app.route("/edit_practice/<int:id>", methods=["GET", "POST"])
def edit_practice(id):

    if "username" not in session:
        return redirect("/login")

    if request.method == "POST":

        language = request.form["language"]
        topic = request.form["topic"]
        difficulty = request.form["difficulty"]
        duration = request.form["duration"]
        status = request.form["status"]
        notes = request.form["notes"]

        sql = """
        UPDATE practice
        SET
            language=?,
            topic=?,
            difficulty=?,
            duration=?,
            status=?,
            notes=?
        WHERE id=?
        AND username=?
        """

        values = (
            language,
            topic,
            difficulty,
            duration,
            status,
            notes,
            id,
            session["username"]
        )

        cursor.execute(sql, values)
        conn.commit()

        return redirect("/dashboard")

    cursor.execute("""
        SELECT *
        FROM practice
        WHERE id=?
        AND username=?
    """, (id, session["username"]))

    practice = cursor.fetchone()

    if practice is None:
        return "Practice record not found", 404

    return render_template(
        "edit_practice.html",
        practice=practice
    )
    
@app.route("/delete_practice/<int:id>")
def delete_practice(id):

    if "username" not in session:
        return redirect("/login")

    sql = """
    DELETE FROM practice
    WHERE id=? AND username=?
    """

    cursor.execute(sql, (id, session["username"]))
    conn.commit()

    return redirect("/dashboard")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        fullname = request.form["fullname"]
        email = request.form["email"]
        username = request.form["username"]

        password = request.form["password"]
        confirm = request.form["confirm_password"]

        if password != confirm:
            return "Passwords do not match"

        cursor.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        )

        user = cursor.fetchone()

        if user:
            return "Username already exists"

        cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        email_exist = cursor.fetchone()

        if email_exist:
            return "Email already registered"

        password = generate_password_hash(password)

        sql = """
        INSERT INTO users(fullname, email, username, password)
        VALUES (?, ?, ?, ?)
        """

        values = (
            fullname,
            email,
            username,
            password
        )

        cursor.execute(sql, values)
        conn.commit()

        return redirect("/login")

    return render_template("register.html")

@app.route("/add_practice", methods=["GET", "POST"])
def add_practice():

    if "username" not in session:
        return redirect("/login")

    if request.method == "POST":

        language = request.form["language"]
        topic = request.form["topic"]
        difficulty = request.form["difficulty"]
        duration = request.form["duration"]
        status = request.form["status"]
        notes = request.form["notes"]

        username = session["username"]

        sql = """
        INSERT INTO practice
        (username, language, topic, difficulty, duration, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        values = (
            username,
            language,
            topic,
            difficulty,
            duration,
            status,
            notes
        )

        cursor.execute(sql, values)
        conn.commit()

        return redirect("/dashboard")

    return render_template("add_practice.html")

if __name__ == "__main__":
    app.run(debug=True)