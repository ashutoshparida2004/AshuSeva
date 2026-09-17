import sqlite3
from datetime import datetime

connection = sqlite3.connect("database/careflow.db")
cursor = connection.cursor()

cursor.execute("""
    SELECT
        token_number,
        status,
        service_started_at,
        completed_at
    FROM appointments
    WHERE service_started_at IS NOT NULL
    AND completed_at IS NOT NULL
    ORDER BY appointment_id
""")

appointments = cursor.fetchall()

for appointment in appointments:

    token = appointment[0]
    status = appointment[1]
    started = appointment[2]
    completed = appointment[3]

    start_time = datetime.strptime(
        started,
        "%Y-%m-%d %H:%M:%S"
    )

    end_time = datetime.strptime(
        completed,
        "%Y-%m-%d %H:%M:%S"
    )

    duration = (end_time - start_time).total_seconds() / 60

    print(
        token,
        "|",
        status,
        "| Consultation Time:",
        round(duration, 2),
        "minutes"
    )

connection.close()