from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import os

app = Flask(__name__)

app.secret_key="smartcodingtracker123"

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="smart_coding_tracker",
    port=3306
)

cursor = conn.cursor()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    
    if request.method == "POST":
        
        username = request.form["username"]
        password = request.form["password"]
        
        sql = "SELECT * FROM users WHERE username=%s"
        
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
        "SELECT COUNT(*) FROM practice WHERE username=%s",
        (username,)
    )
    total_topics = cursor.fetchone()[0]

    # Total Practice Time
    cursor.execute(
        "SELECT IFNULL(SUM(duration),0) FROM practice WHERE username=%s",
        (username,)
    )
    total_time = cursor.fetchone()[0]

    # Completed Count
    cursor.execute(
        "SELECT COUNT(*) FROM practice WHERE username=%s AND status='Completed'",
        (username,)
    )
    completed = cursor.fetchone()[0]

    # Pending Count
    cursor.execute(
        "SELECT COUNT(*) FROM practice WHERE username=%s AND status='Pending'",
        (username,)
    )
    pending = cursor.fetchone()[0]
    
    # Recent Practice History
    cursor.execute("""
    SELECT id, language, topic, difficulty,
    duration, status, created_at
    FROM practice
    WHERE username=%s
    ORDER BY id DESC
    """,(username,))

    practice_list = cursor.fetchall()

    return render_template(
        "dashboard.html",
        fullname=session["fullname"],
        total_topics=total_topics,
        total_time=total_time,
        completed=completed,
        pending=pending,
        practice_list=practice_list
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

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

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
            language=%s,
            topic=%s,
            difficulty=%s,
            duration=%s,
            status=%s,
            notes=%s
        WHERE id=%s
        AND username=%s
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
    
    sql = """
    SELECT *
    FROM practice
    WHERE id=%s
    AND username=%s
    """

    cursor.execute(sql, (id, session["username"]))

    practice = cursor.fetchone()

    return render_template(
        "edit_practice.html",
        practice=practice
    )

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        fullname = request.form["fullname"]
        email = request.form["email"]
        username = request.form["username"]

        password = request.form["password"]
        confirm = request.form["confirm_password"]

        # Password Match Check
        if password != confirm:
            return "Passwords do not match"

        # Username Already Exists Check
        cursor.execute(
            "SELECT * FROM users WHERE username=%s",
            (username,)
        )

        user = cursor.fetchone()

        if user:
            return "Username already exists"

        # Email Already Exists Check
        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        email_exist = cursor.fetchone()

        if email_exist:
            return "Email already registered"

        # Password Hash
        password = generate_password_hash(password)

        sql = """
        INSERT INTO users(fullname, email, username, password)
        VALUES (%s, %s, %s, %s)
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
        VALUES (%s, %s, %s, %s, %s, %s, %s)
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