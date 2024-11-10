from flask import Flask, url_for, render_template, request, redirect, session, flash
from flask_bootstrap import Bootstrap
import bcrypt
import sqlite3
from flask_session import Session
from datetime import datetime
from db import init_db

app = Flask(__name__)
app.secret_key = 'your_secret_key'
Bootstrap(app)
app.config['SESSION_TYPE'] = 'filesystem' 
app.config['SESSION_PERMANENT'] = False
Session(app)

@app.route('/')
def index():
    return render_template('/index.html')

from datetime import datetime

@app.route('/home')
def home():
    if 'email' not in session:
        return redirect('/user_login')
    
    role = session.get('role')
    if role is None:
        flash('Role is not defined. Please log in again.', 'danger')
        return redirect('/user_login')

    # Get the current date in the correct format
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    ongoing_consultation = None
    upcoming_consultations = None

    if role == 'Patient':
        with sqlite3.connect('healthcare.db') as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM Consultations WHERE patient_id = ? AND status = "Ongoing"', (get_user_id_from_email(session['email']),))
            ongoing_consultation = cur.fetchone()

    elif role == 'Therapist':
        with sqlite3.connect('healthcare.db') as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM Consultations WHERE therapist_id = ? AND date >= ? ORDER BY date ASC', (get_therapist_id_from_email(session['email']), current_date))
            upcoming_consultations = cur.fetchall()

    return render_template('home.html', ongoing_consultation=ongoing_consultation, upcoming_consultations=upcoming_consultations)


@app.route('/user_signup', methods=['GET', 'POST'])
def user_signup():
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
        age = request.form['age']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password == confirm_password:
            # Hash the password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            # Check if the email already exists in the database
            with sqlite3.connect('healthcare.db') as conn:
                cur = conn.cursor()
                cur.execute('SELECT * FROM Users WHERE email = ?', (email,))
                existing_user = cur.fetchone()

                if existing_user:
                    flash('Email is already registered.', 'danger')
                else:
                    # Insert the new user record into the database
                    cur.execute('''
                        INSERT INTO Users (fname, lname, email, age, password)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (fname, lname, email, age, hashed_password))
                    conn.commit()
                    flash('User account created successfully. Please log in.', 'success')
                    return redirect('/user_login')  # Redirect to the user login page
        else:
            flash('Passwords do not match. Please try again.', 'danger')

    return render_template('user_signup.html')

@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check the credentials against the database
        with sqlite3.connect('healthcare.db') as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM Users WHERE email = ?', (email,))
            user = cur.fetchone()

            if user and bcrypt.checkpw(password.encode('utf-8'), user[5]):  # Check hashed password
                
                
                flash('Login successful!', 'success')
                session['role'] = 'Patient'
                return redirect('/home')  # Redirect to home page
            else:
                flash('Invalid credentials. Please try again.', 'danger')

    return render_template('user_login.html')

@app.route('/t_login', methods=['GET', 'POST'])
def t_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')

        with sqlite3.connect('healthcare.db') as conn:
            cur = conn.cursor()
            cur.execute('SELECT password FROM Therapists WHERE email = ?', (email,))
            data = cur.fetchone()
            
            if data and bcrypt.checkpw(password, data[0]):
                session['email'] = email
                flash('Login successful!', 'success')
                session['role'] = 'Therapist'
                return redirect('/home')
            else:
                flash('Invalid credentials. Please try again.', 'danger')

    return render_template('t_login.html')

@app.route('/t_signup', methods=['GET', 'POST'])
def t_signup():
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
        session['signup_data'] = {'fname': fname, 'lname': lname, 'email': email}
        return redirect('/t_signup_experience')

    return render_template('t_signup.html')

@app.route('/t_signup_experience', methods=['GET', 'POST'])
def t_signup_experience():
    if request.method == 'POST':
        exp = request.form['experience']
        qualifications = request.form['qualifications']
        
        # Ensure the qualifications are being set correctly
        session['signup_data'].update({'exp': exp, 'qualifications': qualifications})

        # Debugging output: Print the session data to check if 'qualifications' is set
        print(f"Session data after update: {session['signup_data']}")

        return redirect('/t_signup_password')

    return render_template('t_signup_experience.html')


@app.route('/t_signup_password', methods=['GET', 'POST'])
def t_signup_password():

    signup_data = session.get('signup_data', {})
    print(f"Session data in /t_signup_password: {signup_data}")

    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password == confirm_password:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            signup_data = session.get('signup_data')

            # Check if all keys are in the session data
            if True:
                # Print to terminal for manual confirmation
                print(f"Name: {signup_data['fname']} {signup_data['lname']}")
                print(f"Qualifications: {signup_data['qualifications']}")
                
                user_confirm = input("Approve this therapist? (yes/no): ")
                
                if user_confirm.lower() == 'yes':
                    with sqlite3.connect('healthcare.db') as conn:
                        cur = conn.cursor()
                        cur.execute(''' 
                            INSERT INTO Therapists (email, fname, lname, exp, password, qualifications)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (signup_data['email'], signup_data['fname'], signup_data['lname'], signup_data['exp'], hashed_password, signup_data['qualifications']))
                        conn.commit()
                    flash('Signup successful! Please log in.', 'success')
                    return redirect('/t_login')
                else:
                    flash('Signup not approved.', 'warning')
                    return redirect('/t_signup')
            else:
                flash('Missing signup data. Please complete the form properly.', 'danger')
                return redirect('/t_signup_experience')

        else:
            flash('Passwords do not match. Please try again.', 'danger')

    return render_template('t_signup_password.html')




@app.route('/forum', methods=['GET', 'POST'])
def forum():
    if request.method == 'POST':
        # Insert new post into the database
        post_text = request.form['post_text']
        with sqlite3.connect('healthcare.db') as conn:
            cur = conn.cursor()
            cur.execute('INSERT INTO Post (text, uid) VALUES (?, NULL)', (post_text,))
            conn.commit()
        return redirect('/forum')

    # Fetch all posts from the database
    with sqlite3.connect('healthcare.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT post_id, text FROM Post ORDER BY post_id DESC')
        posts = cur.fetchall()

    return render_template('forum.html', posts=posts)

@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post_detail(post_id):
    if request.method == 'POST':
        # Insert new comment into the database
        comment_text = request.form['comment_text']
        with sqlite3.connect('healthcare.db') as conn:
            cur = conn.cursor()
            cur.execute('INSERT INTO Comment (text, uid, post_id) VALUES (?, NULL, ?)', (comment_text, post_id))
            conn.commit()
        return redirect(f'/post/{post_id}')

    # Fetch the post and comments
    with sqlite3.connect('healthcare.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT text FROM Post WHERE post_id = ?', (post_id,))
        post = cur.fetchone()
        cur.execute('SELECT text FROM Comment WHERE post_id = ?', (post_id,))
        comments = cur.fetchall()

    return render_template('post_detail.html', post=post, comments=comments)

@app.route('/therapists', methods=['GET'])
def therapists():
    with sqlite3.connect('healthcare.db') as conn:
        conn.row_factory = sqlite3.Row  # To access columns by name
        cur = conn.cursor()
        cur.execute('''
            SELECT id, email, fname, lname, exp, qualifications
            FROM Therapists
            ORDER BY lname ASC, fname ASC
        ''')
        therapists = cur.fetchall()

    return render_template('therapists.html', therapists = therapists)

@app.route('/therapist/<int:therapist_id>', methods=['GET', 'POST'])
def therapist_detail(therapist_id):
    # Fetch the therapist's details from the database
    with sqlite3.connect('healthcare.db') as conn:
        cur = conn.cursor()
        therapist = get_therapist_by_id(therapist_id)

        # If therapist not found, redirect to an error page or the therapist list
        if not therapist:
            return redirect(url_for('therapists'))

        # If the user is booking a consultation
        if request.method == 'POST':
            user_id = session.get('user_id')
            # Insert consultation request into the database
            cur.execute('''
                INSERT INTO Consultations (patient_id, therapist_id, status)
                VALUES (?, ?, 'Upcoming')
            ''', (user_id, therapist_id))
            conn.commit()

            # Redirect to the consultation requests page for the user
            return redirect(url_for('consultation_requests'))

    return render_template('therapist_detail.html', therapist=therapist)

@app.route('/consultation_requests', methods=['GET'])
def consultation_requests():
    user_id = session.get('user_id')  # Assuming the current user is logged in
    with sqlite3.connect('healthcare.db') as conn:
        cur = conn.cursor()
        # Get all consultations requested by the current user
        cur.execute('''
            SELECT c.consultation_id, t.fname, t.lname, c.status 
            FROM Consultations c
            JOIN Therapists t ON c.therapist_id = t.id
            WHERE c.patient_id = ?
        ''', (user_id,))
        consultations = cur.fetchall()
    
    return render_template('consultation_requests.html', consultations=consultations)


def get_therapist_by_id(therapist_id):
    with sqlite3.connect('healthcare.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Therapists WHERE id = ?", (therapist_id,))
        therapist = cur.fetchone()
        if therapist:
            return {
                'id': therapist[0],
                'email': therapist[1],
                'fname': therapist[2],
                'lname': therapist[3],
                'exp': therapist[4],
                'password': therapist[5],  # Omit this in production or sensitive views
                'qualifications': therapist[6]
            }
        return None

@app.route('/therapist/consultation_requests/<int:therapist_id>', methods=['GET', 'POST'])
def therapist_consultation_requests(therapist_id):
    if request.method == 'POST':
        consultation_id = request.form.get('consultation_id')
        action = request.form.get('action')  # Accept or reject

        with sqlite3.connect('healthcare.db') as conn:
            cur = conn.cursor()

            # Update the status of the consultation request
            if action == 'accept':
                cur.execute('''
                    UPDATE Consultations
                    SET status = 'Ongoing'
                    WHERE consultation_id = ?
                ''', (consultation_id,))
            elif action == 'reject':
                cur.execute('''
                    DELETE FROM Consultations
                    WHERE consultation_id = ?
                ''', (consultation_id,))

            conn.commit()

        return redirect(url_for('therapist_consultation_requests', therapist_id=therapist_id))

    with sqlite3.connect('healthcare.db') as conn:
        cur = conn.cursor()
        # Get all consultation requests for this therapist
        cur.execute('''
            SELECT c.consultation_id, u.fname, u.lname, c.status
            FROM Consultations c
            JOIN Users u ON c.patient_id = u.user_id
            WHERE c.therapist_id = ?
        ''', (therapist_id,))
        consultations = cur.fetchall()

    return render_template('therapist_consultation_requests.html', consultations=consultations)

@app.route('/logout')
def logout():
    # Remove the user_id from the session to log them out
    session.clear()
    
    # Redirect to the login page or home page
    return redirect(url_for('index'))  # Redirect to login page (or home page)

def get_user_id_from_email(email):
    # Connect to the SQLite database
    with sqlite3.connect('healthcare.db') as conn:
        cur = conn.cursor()
        # Query to get the user_id based on the email
        cur.execute('SELECT user_id FROM Users WHERE email = ?', (email,))
        result = cur.fetchone()  # Fetch the first matching row
        if result:
            return result[0]  # Return the user_id
        else:
            return None
        
def get_therapist_id_from_email(email):
    # Connect to the SQLite database
    with sqlite3.connect('healthcare.db') as conn:
        cur = conn.cursor()
        # Query to get the therapist_id based on the email
        cur.execute('SELECT id FROM Therapists WHERE email = ?', (email,))
        result = cur.fetchone()  # Fetch the first matching row
        if result:
            return result[0]  # Return the therapist_id
        else:
            return None

if __name__ == '__main__':
    init_db()
    app.run()