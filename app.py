from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import date, timedelta
import os

app = Flask(__name__)

DB_FILE = "habits.db"

# Function to get database connection
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # So we can access columns by name
    return conn

# Function to create table if it doesn't exist
def init_db():
    if not os.path.exists(DB_FILE):
        with get_db() as db:
            db.execute("""
            CREATE TABLE habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                streak INTEGER DEFAULT 0,
                last_completed TEXT
            )
            """)
        print("Database created successfully!")

# Initialize database on app start
init_db()

# Home route
@app.route("/", methods=["GET", "POST"])
def index():
    db = get_db()

    if request.method == "POST":
        habit = request.form["habit"].strip()
        if habit:
            db.execute(
                "INSERT INTO habits (name, completed, streak) VALUES (?, ?, ?)",
                (habit, 0, 0)
            )
            db.commit()
        return redirect("/")

    habits = db.execute("SELECT * FROM habits").fetchall()

    total = len(habits)
    completed = sum(1 for h in habits if h["completed"] == 1)
    progress = int((completed / total) * 100) if total > 0 else 0

    return render_template(
        "index.html",
        habits=habits,
        total=total,
        completed=completed,
        progress=progress
    )

# Complete habit route
@app.route("/complete/<int:habit_id>")
def complete(habit_id):
    db = get_db()
    habit = db.execute(
        "SELECT streak, last_completed, completed FROM habits WHERE id = ?",
        (habit_id,)
    ).fetchone()
    
    today = date.today()
    yesterday = today - timedelta(days=1)

    if habit["completed"] == 1:
        # Already completed today
        streak = habit["streak"]
    else:
        if habit["last_completed"]:
            last_date = date.fromisoformat(habit["last_completed"])
            if last_date == yesterday:
                streak = habit["streak"] + 1
            else:
                streak = 1
        else:
            streak = 1

    db.execute(
        "UPDATE habits SET completed = 1, streak = ?, last_completed = ? WHERE id = ?",
        (streak, today.isoformat(), habit_id)
    )
    db.commit()
    return redirect("/")

# Delete habit route
@app.route("/delete/<int:habit_id>")
def delete(habit_id):
    db = get_db()
    db.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
    db.commit()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)


