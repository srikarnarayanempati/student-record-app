from flask import Flask, render_template, request, redirect, url_for, flash, Response
import mysql.connector
from dotenv import load_dotenv
import os
import csv
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask import make_response
from flask import send_file  # already used in CSV export


load_dotenv()
password = os.getenv("DB_PASSWORD")

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

# MySQL Configuration
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Srik@r2004",   
    database="student_db"
)
cursor = db.cursor()

@app.route('/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        roll_no = request.form['roll_no']
        department = request.form['department']
        marks = request.form['marks']

        cursor = db.cursor()
        query = "INSERT INTO students (name, roll_no, department, marks) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (name, roll_no, department, marks))
        db.commit()
        flash("Student added successfully!", "success")
        return redirect('/')
    return render_template('add_student.html')

@app.route('/')
def home():
    query = request.args.get('q')
    cursor = db.cursor(dictionary=True)

    if query:
        sql = "SELECT * FROM students WHERE name LIKE %s OR roll_no LIKE %s"
        like_query = f"%{query}%"
        cursor.execute(sql, (like_query, like_query))
        students = cursor.fetchall()
        if not students:
            flash("No students found matching your search.", "danger")
    else:
        cursor.execute("SELECT * FROM students")
        students = cursor.fetchall()

    return render_template('home.html', students=students)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form['name']
        roll_no = request.form['roll_no']
        department = request.form['department']
        marks = request.form['marks']

        query = "UPDATE students SET name=%s, roll_no=%s, department=%s, marks=%s WHERE id=%s"
        cursor.execute(query, (name, roll_no, department, marks, id))
        db.commit()
        flash("Student details updated!", "info")
        return redirect('/')

    cursor.execute("SELECT * FROM students WHERE id = %s", (id,))
    student = cursor.fetchone()
    return render_template('edit.html', student=student)

@app.route('/delete/<int:id>')
def delete_student(id):
    cursor = db.cursor()
    cursor.execute("DELETE FROM students WHERE id = %s", (id,))
    db.commit()
    flash("Student deleted!", "warning")
    return redirect('/')


@app.route('/view/<int:id>')
def view_student(id):
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students WHERE id = %s", (id,))
    student = cursor.fetchone()
    if not student:
        flash("Student not found!", "danger")
        return redirect(url_for('home'))
    return render_template("view.html", student=student)

@app.route('/export_csv')
def export_csv():
    cursor = db.cursor()
    cursor.execute("SELECT * FROM students")
    results = cursor.fetchall()

    # Create an in-memory string buffer
    output = io.StringIO()
    writer = csv.writer(output)

    # Write headers and rows
    writer.writerow(['ID', 'Name', 'Roll No', 'Department', 'Marks'])
    for row in results:
        writer.writerow(row)

    # Move to beginning of stream
    output.seek(0)

    return Response(output, mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=students.csv'})

@app.route('/export/pdf')
def export_pdf():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, height - 40, "Student Records")

    pdf.setFont("Helvetica", 12)
    y = height - 80
    pdf.drawString(50, y, "ID")
    pdf.drawString(100, y, "Name")
    pdf.drawString(250, y, "Roll No")
    pdf.drawString(350, y, "Dept")
    pdf.drawString(450, y, "Marks")

    y -= 20
    for student in students:
        if y < 50:  # page break
            pdf.showPage()
            y = height - 40
        pdf.drawString(50, y, str(student['id']))
        pdf.drawString(100, y, student['name'])
        pdf.drawString(250, y, student['roll_no'])
        pdf.drawString(350, y, student['department'])
        pdf.drawString(450, y, str(student['marks']))
        y -= 20

    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="students.pdf", mimetype='application/pdf')


if __name__ == '__main__':
    app.run(debug=True)
