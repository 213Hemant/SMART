from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_NAME = 'goals.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                type TEXT CHECK(type IN ('short-term', 'long-term')) NOT NULL,
                specific TEXT,
                measurable TEXT,
                achievable TEXT,
                relevant TEXT,
                time_bound TEXT,
                completed INTEGER DEFAULT 0,
                created_at TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER,
                note TEXT,
                created_at TEXT,
                FOREIGN KEY(goal_id) REFERENCES goals(id) ON DELETE CASCADE
            )
        ''')

# Route: Add Goal Form (Index Page)
@app.route('/')
def index():
    return render_template('index.html')

# Route: View All Goals
@app.route('/goals')
def view_goals():
    filter_type = request.args.get('filter')
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        
        if filter_type in ['short-term', 'long-term']:
            cur.execute("SELECT * FROM goals WHERE type = ? ORDER BY created_at DESC", (filter_type,))
        else:
            cur.execute("SELECT * FROM goals ORDER BY created_at DESC")
        
        goals = cur.fetchall()

        checkins = {}
        for goal in goals:
            cur.execute("SELECT * FROM checkins WHERE goal_id = ? ORDER BY created_at DESC", (goal[0],))
            checkins[goal[0]] = cur.fetchall()
    
    return render_template('goals.html', goals=goals, checkins=checkins, filter=filter_type)

# Route: Add New Goal
@app.route('/add', methods=['POST'])
def add_goal():
    data = {
        'title': request.form['title'],
        'description': request.form.get('description', ''),
        'type': request.form['type'],
        'specific': request.form.get('specific', ''),
        'measurable': request.form.get('measurable', ''),
        'achievable': request.form.get('achievable', ''),
        'relevant': request.form.get('relevant', ''),
        'time_bound': request.form.get('time_bound', ''),
        'created_at': datetime.now().isoformat()
    }
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''
            INSERT INTO goals 
            (title, description, type, specific, measurable, achievable, relevant, time_bound, created_at)
            VALUES (:title, :description, :type, :specific, :measurable, :achievable, :relevant, :time_bound, :created_at)
        ''', data)
    return redirect(url_for('view_goals'))

# Route: Delete Goal
@app.route('/delete/<int:goal_id>')
def delete_goal(goal_id):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
    return redirect(url_for('view_goals'))

# Route: Edit Goal
@app.route('/edit/<int:goal_id>', methods=['GET', 'POST'])
def edit_goal(goal_id):
    if request.method == 'POST':
        data = (
            request.form['title'],
            request.form.get('description', ''),
            request.form['type'],
            request.form.get('specific', ''),
            request.form.get('measurable', ''),
            request.form.get('achievable', ''),
            request.form.get('relevant', ''),
            request.form.get('time_bound', ''),
            goal_id
        )
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute('''
                UPDATE goals SET
                title = ?, description = ?, type = ?, specific = ?, measurable = ?, 
                achievable = ?, relevant = ?, time_bound = ?
                WHERE id = ?
            ''', data)
        return redirect(url_for('view_goals'))
    else:
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
            goal = cur.fetchone()
        return render_template('edit.html', goal=goal)

# Route: Toggle Completion
@app.route('/toggle_complete/<int:goal_id>')
def toggle_complete(goal_id):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT completed FROM goals WHERE id = ?", (goal_id,))
        current = cur.fetchone()[0]
        conn.execute("UPDATE goals SET completed = ? WHERE id = ?", (1 - current, goal_id))
    return redirect(url_for('view_goals'))

# Route: Add Check-in
@app.route('/checkin/<int:goal_id>', methods=['POST'])
def add_checkin(goal_id):
    note = request.form['note']
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''
            INSERT INTO checkins (goal_id, note, created_at)
            VALUES (?, ?, ?)
        ''', (goal_id, note, datetime.now().isoformat()))
    return redirect(url_for('view_goals'))

# Route: Help Page
@app.route('/help')
def help_page():
    return render_template('help.html')

# Entry Point
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
