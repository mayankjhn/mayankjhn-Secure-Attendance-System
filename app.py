from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import qrcode
import os
import random
import string
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'teacher' or 'student'

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# Generate random QR code value
def generate_qr_value():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

# Store current QR code value and expiration
generated_qr = {'value': '', 'expires_at': datetime.utcnow()}

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username, password=password).first()
    if user:
        session['user_id'] = user.id
        session['role'] = user.role
        if user.role == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return 'Invalid credentials'

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/teacher')
def teacher_dashboard():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('home'))
    students_attendance = Attendance.query.all()
    return render_template('teacher.html', qr_value=generated_qr['value'], students=students_attendance)

@app.route('/generate_qr')
def generate_qr():
    global generated_qr
    generated_qr['value'] = generate_qr_value()
    generated_qr['expires_at'] = datetime.utcnow() + timedelta(seconds=10)
    img = qrcode.make(generated_qr['value'])
    img.save('static/qr.png')
    return jsonify({'qr_value': generated_qr['value']})

@app.route('/student')
def student_dashboard():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('home'))
    student_attendance = Attendance.query.filter_by(student_id=session['user_id']).all()
    return render_template('student.html', attendance=student_attendance)

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    scanned_qr = request.json['qr_value']
    if scanned_qr == generated_qr['value'] and datetime.utcnow() <= generated_qr['expires_at']:
        new_attendance = Attendance(student_id=session['user_id'], subject='Sample Subject')
        db.session.add(new_attendance)
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'failed'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
