import sqlite3

def init_db():
    with sqlite3.connect('healthcare.db') as conn:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS Therapists (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            email TEXT NOT NULL,
            fname VARCHAR(100),
            lname VARCHAR(100),  
            exp INTEGER,
            password VARCHAR(60) NOT NULL,
            qualifications VARCHAR(500) NOT NULL
        );''')
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS backlog (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            email TEXT NOT NULL,
            fname VARCHAR(100),
            lname VARCHAR(100),  
            exp INTEGER,
            password VARCHAR(60) NOT NULL,
            qualifications VARCHAR(500) NOT NULL
        );''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                fname VARCHAR(100) NOT NULL, 
                lname VARCHAR(100) NOT NULL, 
                email VARCHAR(100) NOT NULL UNIQUE,
                age INTEGER CHECK(age > 18),
                password VARCHAR(60) NOT NULL,
                therapist_id INTEGER NOT NULL DEFAULT 0,
                severity INTEGER DEFAULT 5,
                date_of_joining DATE NOT NULL DEFAULT CURRENT_DATE, 
                FOREIGN KEY (therapist_id) REFERENCES Therapists(id)
            );
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS Consultations (
                consultation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER,
                therapist_id INTEGER,
                status TEXT CHECK(status IN ('Ongoing', 'Upcoming')) NOT NULL,
                start_date DATE,
                progress INTEGER CHECK(progress >= 0 AND progress <= 100),
                FOREIGN KEY (patient_id) REFERENCES Users(user_id),
                FOREIGN KEY (therapist_id) REFERENCES Therapists(id)
            );
        ''')
        
        cur.execute ('''
                CREATE TABLE IF NOT EXISTS Diagnosis (
                diagnosis_id INTEGER PRIMARY KEY,
                diagnosis_name VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                severity INTEGER
                    );''')
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS Post (
                post_id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                uid INTEGER,
                role TEXT CHECK(role IN ('Patient', 'Therapist')) NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (uid) REFERENCES Users(user_id)
            );
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS Comment (
                text TEXT NOT NULL,
                uid INTEGER,
                post_id INTEGER,
                FOREIGN KEY (post_id) REFERENCES Post(post_id)
            );
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS Admin (
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            );
        ''')
        cur.execute('''CREATE TABLE IF NOT EXISTS notifications (
    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    therapist_id INTEGER NOT NULL,
    consultation_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    status TEXT DEFAULT 'Unread',  -- Status can be 'Unread' or 'Read'
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (therapist_id) REFERENCES therapists(id),
    FOREIGN KEY (consultation_id) REFERENCES consultations(consultation_id)
);
''')

        conn.commit()
