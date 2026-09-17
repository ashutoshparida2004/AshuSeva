import sqlite3


DATABASE = "database/careflow.db"


def create_database():
    connection = sqlite3.connect(DATABASE)

    cursor = connection.cursor()

    # Create patients table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            phone TEXT NOT NULL
        )
    """)

        # Create appointments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            department_id INTEGER NOT NULL,
            token_number TEXT,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
            FOREIGN KEY (department_id) REFERENCES departments(department_id)
        )
    """)



    # Create departments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            department_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)

    # Add hospital departments
    departments = [
        "Cardiology",
        "Neurology",
        "Orthopedics",
        "Gastroenterology",
        "Dermatology",
        "General Medicine",
        "Pediatrics"
    ]

    for department in departments:
        cursor.execute(
            "INSERT OR IGNORE INTO departments (name) VALUES (?)",
            (department,)
        )


    try:
        cursor.execute("""
            ALTER TABLE appointments
            ADD COLUMN token_number TEXT
        """)
    except sqlite3.OperationalError:
        pass

        try:
            cursor.execute("""
            ALTER TABLE appointments
            ADD COLUMN service_started_at TEXT
        """)
        except sqlite3.OperationalError:
            pass

    try:
        cursor.execute("""ALTER TABLE appointments
                ADD COLUMN completed_at TEXT
            """)
    except sqlite3.OperationalError:
        pass

    connection.commit()
    connection.close()
    

if __name__ == "__main__":
    create_database()
    print("CareFlow AI database created successfully!")