# 1. IMPORTS
from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
from model import train_model, predict_risk
from utils.exporter import export_csv
from utils.helper import generate_recommendation
import sqlite3
from flask import Response 
import csv

conn = sqlite3.connect('students.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
''')

conn.commit()
conn.close()

# 2. CREATE FLASK APP
app = Flask(__name__)
app.secret_key = 'abc123mysecret'

# 3. DATABASE FUNCTION
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        math INTEGER,
        science INTEGER,
        english INTEGER,
        attendance INTEGER
    )
    ''')

    conn.commit()
    conn.close()

# 4. CALL DATABASE FUNCTION (IMPORTANT!)
init_db()

@app.route('/dashboard')
def dashboard():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    # your existing code

    conn = sqlite3.connect('database.db')

    search = request.args.get('search')
    filter_type = request.args.get('filter')
    attendance_filter = request.args.get('attendance_filter')

    query = "SELECT * FROM students WHERE 1=1"
    params = []

    if search:
        query += " AND name LIKE ?"
        params.append('%' + search + '%')

    if filter_type == 'risk':
        query += " AND (math < 40 OR science < 40 OR english < 40 OR attendance < 60)"

    elif filter_type == 'topper':
        query += " AND (math + science + english) > 250"

    elif filter_type == 'average':
        query += " AND (math + science + english) BETWEEN 120 AND 250 AND ATTENDANCE >= 60"

    if attendance_filter == 'low':
        query += " AND attendance < 60"

    elif attendance_filter == 'average':
        query += " AND attendance BETWEEN 60 AND 80"

    elif attendance_filter == 'good':
        query += " AND attendance >80"

        query += " ORDER BY name ASC"

    data = conn.execute(query, params).fetchall()
    conn.close()

    return render_template('dashboard.html', students=data)


# Add Student
@app.route('/add', methods=['GET', 'POST'])
def add_student():
    if 'user' not in session:
     return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        math = request.form['math']
        science = request.form['science']
        english = request.form['english']
        attendance = request.form['attendance']

        conn = sqlite3.connect('database.db')
        conn.execute('INSERT INTO students (name, math, science, english, attendance) VALUES (?, ?, ?, ?, ?)',
                     (name, math, science, english, attendance))
        conn.commit()
        conn.close()

        return redirect('/')
    return render_template('add_student.html')

@app.route('/analytics')
def analytics():

    # 🔐 Login check
    if 'user' not in session:
        return redirect(url_for('login'))

    # 📊 Fetch data
    conn = sqlite3.connect('database.db')
    df = pd.read_sql_query('SELECT * FROM students ORDER BY name ASC', conn)
    conn.close()

    # ➕ TOTAL
    df['total'] = df[['math', 'science', 'english']].sum(axis=1)

    # ⚠️ RISK
    df['risk'] = df.apply(
        lambda x: 1 if (x['total'] < 120 or x['attendance'] < 60) else 0,
        axis=1
    )

    # 🏆 TOPPER
    df['topper'] = df['total'].apply(lambda x: 1 if x >= 250 else 0)

    # 📊 CATEGORY (IMPORTANT - brings back Average/At Risk/Topper)
    def get_category(row):
        if row['risk'] == 1:
            return "At Risk"
        elif row['topper'] == 1:
            return "Topper"
        else:
            return "Average"

    df['category'] = df.apply(get_category, axis=1)

    # 🔍 FILTER FEATURE (RESTORED)
    filter_type = request.args.get('filter')
    filtered_df=df.copy()
    if filter_type == "risk":
        df = df[df['category'] == "At Risk"]
    elif filter_type == "topper":
        df = df[df['category'] == "Topper"]
    elif filter_type == "average":
        df = df[df['category'] == "Average"]

    # 💡 RECOMMENDATION
    def get_recommendation(row):
        issues = []

        if row['math'] < 40:
            issues.append("Math")
        if row['science'] < 40:
            issues.append("Science")
        if row['english'] < 40:
            issues.append("English")
        if row['attendance'] < 60:
            issues.append("Attendance")

        return "Improve " + ", ".join(issues) if issues else "Good Performance"

    df['recommendation'] = df.apply(get_recommendation, axis=1)

    # 🥇 TOP STUDENTS WITH RANK
    sorted_df = df.sort_values(by='total', ascending=False)

    top_students = []
    rank = 0
    prev_marks = -1
    count = 0

    for _, row in sorted_df.iterrows():
        count += 1

        if row['total'] != prev_marks:
            rank = count

        student = row.to_dict()
        student['rank'] = rank

        prev_marks = row['total']

        if rank > 5:
            break

        top_students.append(student)

    # 📈 SUMMARY
    avg = int(df['total'].mean()) if not df.empty else 0
    highest = df['total'].max() if not df.empty else 0
    lowest = df['total'].min() if not df.empty else 0

    # 🚀 FINAL
    return render_template(
        'analytics.html',
        data=df.to_dict(orient='records'),
        top_students=top_students,
        avg=avg,
        highest=highest,
        lowest=lowest
    )

@app.route('/export')
def export():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    data = conn.execute("SELECT * FROM students").fetchall()
    conn.close()

    def generate():
        yield 'ID,Name,Math,Science,English,Attendance\n'
        for row in data:
            yield f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]},{row[5]}\n"

    return Response(
        generate(),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=report.csv"}
    )

@app.route('/report')
def report():
    if 'user' not in session:
     return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    df = pd.read_sql_query('SELECT * FROM students', conn)
    conn.close()

    df['total'] = df[['math','science','english']].sum(axis=1)
    df['risk'] = df.apply(lambda x: 1 if (x['total'] < 120 or x['attendance'] < 60) else 0, axis=1)
    df['topper'] = df['total'].apply(lambda x: 1 if x >= 250 else 0)

    from utils.helper import generate_recommendation
    df['recommendation'] = df.apply(generate_recommendation, axis=1)
    return render_template('report.html', data=df.to_dict(orient='records'))

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # ✅ FIXED ADMIN CREDENTIALS
        if username == 'admin' and password == 'admin123':
            session['user'] = username
            session['role'] = 'admin'
            return redirect(url_for('dashboard'))
        else:
            return "Invalid Credentials"

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/delete/<int:id>')
def delete_student(id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM students WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        math = request.form['math']
        science = request.form['science']
        english = request.form['english']
        attendance = request.form['attendance']

        cur.execute("""
            UPDATE students 
            SET name=?, math=?, science=?, english=?, attendance=? 
            WHERE id=?
        """, (name, math, science, english, attendance, id))

        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))

    # GET request
    cur.execute("SELECT * FROM students WHERE id=?", (id,))
    student = cur.fetchone()
    conn.close()

    return render_template('edit.html', student=student)

# 6. RUN APP
if __name__ == '__main__':
    app.run(debug=True)