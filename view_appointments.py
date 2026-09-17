import sqlite3


connection = sqlite3.connect("database/careflow.db")

cursor = connection.cursor()

cursor.execute("""
    SELECT
        appointments.appointment_id,
        patients.name,
        departments.name,
        appointments.appointment_date,
        appointments.appointment_time,
        appointments.status
    FROM appointments
    JOIN patients
        ON appointments.patient_id = patients.patient_id
    JOIN departments
        ON appointments.department_id = departments.department_id
""")

appointments = cursor.fetchall()

for appointment in appointments:
    print(appointment)

connection.close()