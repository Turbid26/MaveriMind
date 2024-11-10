import sqlite3

with sqlite3.connect('healthcare.db') as conn:
    cur = conn.cursor()
    cur.execute('''SELECT fname || " " || lname as name, exp as experience, qualifications 
                   FROM Therapists ORDER BY name ASC''')
    therapists = cur.fetchall()

print(therapists)