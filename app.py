from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

DATABASE = "database/careflow.db"


def get_departments():
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM departments")
    departments = cursor.fetchall()

    connection.close()

    return departments


@app.route("/")
def home():
    departments = get_departments()

    return render_template(
        "index.html",
        departments=departments
    )


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        name = request.form["name"]
        age = request.form["age"]
        gender = request.form["gender"]
        phone = request.form["phone"]
        department_id = request.form["department_id"]

        connection = sqlite3.connect(DATABASE)
        cursor = connection.cursor()

        # Add patient
        cursor.execute("""
            INSERT INTO patients (name, age, gender, phone)
            VALUES (?, ?, ?, ?)
        """, (name, age, gender, phone))

        patient_id = cursor.lastrowid

        # Find the highest token number for this department today
        cursor.execute("""
            SELECT token_number
            FROM appointments
            WHERE department_id = ?
            AND appointment_date = date('now')
            AND token_number IS NOT NULL
            ORDER BY appointment_id DESC
            LIMIT 1
        """, (department_id,))

        last_token = cursor.fetchone()

        if last_token is None:
            next_number = 1
        else:
            last_number = int(last_token[0].split("-")[1])
            next_number = last_number + 1

        # Get department name
        cursor.execute("""
            SELECT name
            FROM departments
            WHERE department_id = ?
        """, (department_id,))

        department = cursor.fetchone()
        department_name = department[0]

        # Create department prefix
        prefix = department_name[:1].upper()
        token_number = f"{prefix}-{next_number:03d}"

        # Add appointment
        cursor.execute("""
            INSERT INTO appointments
            (
                patient_id,
                department_id,
                token_number,
                appointment_date,
                appointment_time,
                status
            )
            VALUES (?, ?, ?, date('now'), time('now'), ?)
        """, (
            patient_id,
            department_id,
            token_number,
            "Waiting"
        ))

        connection.commit()
        connection.close()

        return redirect(url_for(
            "queue",
            token_number=token_number
        ))

    departments = get_departments()

    return render_template(
        "register.html",
        departments=departments
    )


@app.route("/admin")
def admin():

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    # Total patients registered today
    cursor.execute("""
        SELECT COUNT(*)
        FROM appointments
        WHERE appointment_date = date('now')
    """)
    total_patients = cursor.fetchone()[0]

    # Total waiting patients
    cursor.execute("""
        SELECT COUNT(*)
        FROM appointments
        WHERE appointment_date = date('now')
        AND status = 'Waiting'
    """)
    waiting_patients = cursor.fetchone()[0]

    # Total patients currently being served
    cursor.execute("""
        SELECT COUNT(*)
        FROM appointments
        WHERE appointment_date = date('now')
        AND status = 'Serving'
    """)
    serving_patients = cursor.fetchone()[0]

    # Get all departments
    cursor.execute("""
        SELECT department_id, name
        FROM departments
        ORDER BY department_id
    """)

    department_list = cursor.fetchall()

    departments = []

    # Get queue information for each department
    for department in department_list:

        department_id = department[0]
        department_name = department[1]

        # Count waiting patients
        cursor.execute("""
            SELECT COUNT(*)
            FROM appointments
            WHERE department_id = ?
            AND appointment_date = date('now')
            AND status = 'Waiting'
        """, (department_id,))

        waiting_count = cursor.fetchone()[0]

        estimated_wait = waiting_count * 5

        # Find currently serving patient
        cursor.execute("""
            SELECT token_number
            FROM appointments
            WHERE department_id = ?
            AND appointment_date = date('now')
            AND status = 'Serving'
            ORDER BY appointment_id
            LIMIT 1
        """, (department_id,))

        serving = cursor.fetchone()

        if serving is None:
            now_serving = "None"
        else:
            now_serving = serving[0]

        departments.append(
            (
                department_id,
                department_name,
                waiting_count,
                now_serving,
                estimated_wait
            )
        )

    connection.close()

    return render_template(
        "admin.html",
        total_patients=total_patients,
        waiting_patients=waiting_patients,
        serving_patients=serving_patients,
        departments=departments
    )


@app.route("/call-next/<int:department_id>", methods=["POST"])
def call_next(department_id):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    # Find the first waiting patient in this department
    cursor.execute("""
        SELECT appointment_id
        FROM appointments
        WHERE department_id = ?
        AND appointment_date = date('now')
        AND status = 'Waiting'
        ORDER BY appointment_id
        LIMIT 1
    """, (department_id,))

    patient = cursor.fetchone()

    if patient is None:
        connection.close()
        return redirect(url_for("admin"))

    appointment_id = patient[0]

    # Change patient status to Serving
    cursor.execute("""
        UPDATE appointments
        SET status = 'Serving',
            service_started_at = ?
        WHERE appointment_id = ?
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        appointment_id
    ))

    connection.commit()
    connection.close()

    return redirect(url_for("admin"))


@app.route("/complete-current/<int:department_id>", methods=["POST"])
def complete_current(department_id):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    # Find the currently serving patient in this department
    cursor.execute("""
        SELECT appointment_id
        FROM appointments
        WHERE department_id = ?
        AND appointment_date = date('now')
        AND status = 'Serving'
        ORDER BY appointment_id
        LIMIT 1
    """, (department_id,))

    patient = cursor.fetchone()

    if patient is None:
        connection.close()
        return redirect(url_for("admin"))

    appointment_id = patient[0]

    # Mark patient as completed
    cursor.execute("""
        UPDATE appointments
        SET status = 'Completed',
            completed_at = ?
        WHERE appointment_id = ?
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        appointment_id
    ))

    connection.commit()
    connection.close()

    return redirect(url_for("admin"))


@app.route("/queue/<token_number>")
def queue(token_number):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    # Find this appointment
    cursor.execute("""
    SELECT
        appointments.appointment_id,
        appointments.department_id,
        appointments.status,
        departments.name,
        patients.name,
        patients.age
    FROM appointments
    JOIN departments
        ON appointments.department_id = departments.department_id
    JOIN patients
        ON appointments.patient_id = patients.patient_id
    WHERE appointments.token_number = ?
    AND appointments.appointment_date = date('now')
""", (token_number,))

    appointment = cursor.fetchone()

    if appointment is None:
        connection.close()
        return "Token not found."

    
    appointment_id = appointment[0]
    department_id = appointment[1]
    status = appointment[2]
    department_name = appointment[3]
    patient_name = appointment[4]
    patient_age = appointment[5]

    # Find currently serving 
    cursor.execute("""
        SELECT token_number
        FROM appointments
        WHERE department_id = ?
        AND appointment_date = date('now')
        AND status = 'Serving'
        ORDER BY appointment_id
        LIMIT 1
    """, (department_id,))

    serving = cursor.fetchone()

    if serving is None:
        now_serving = "Not started"
    else:
        now_serving = serving[0]

    # Count waiting patients before this patient
    cursor.execute("""
        SELECT COUNT(*)
        FROM appointments
        WHERE department_id = ?
        AND appointment_date = date('now')
        AND status = 'Waiting'
        AND appointment_id < ?
    """, (department_id, appointment_id))

    patients_ahead = cursor.fetchone()[0]

    # ---------------------------------------------------------
    # DYNAMIC TIME ESTIMATION
    # OPD starts at 8:00 AM
    # Average consultation time = 5 minutes
    # Recommended arrival = 10 minutes before estimated turn
    # ---------------------------------------------------------

    average_consultation_time = 5
    arrival_buffer = 10

    current_time = datetime.now()

    # Today's OPD starting time
    today_opd_start = current_time.replace(
        hour=8,
        minute=0,
        second=0,
        microsecond=0
    )

    # If the patient's consultation is already in progress
    if status == "Serving":

        estimated_wait = 0
        estimated_turn_time = "Now"
        recommended_arrival_time = "Now"

    # If consultation is already completed
    elif status == "Completed":

        estimated_wait = 0
        estimated_turn_time = "Completed"
        recommended_arrival_time = "-"

    # Patient is still waiting
    else:

        # Find when the current serving patient's consultation started
        cursor.execute("""
            SELECT service_started_at
            FROM appointments
            WHERE department_id = ?
            AND appointment_date = date('now')
            AND status = 'Serving'
            ORDER BY appointment_id
            LIMIT 1
        """, (department_id,))

        serving_details = cursor.fetchone()

        if serving_details is not None and serving_details[0]:

            try:
                serving_start = datetime.strptime(
                    serving_details[0],
                    "%Y-%m-%d %H:%M:%S"
                )

                # Expected completion of current consultation
                serving_end = serving_start + timedelta(
                    minutes=average_consultation_time
                )

                # If the expected time has already passed,
                # continue from the current time.
                if serving_end < current_time:
                    serving_end = current_time

                estimated_turn = serving_end + timedelta(
                    minutes=patients_ahead * average_consultation_time
                )

            except ValueError:

                # Fallback if timestamp cannot be read
                estimated_turn = current_time + timedelta(
                    minutes=(patients_ahead + 1)
                    * average_consultation_time
                )

        else:

            # Nobody is currently being served.
            # If it is before 8 AM, start calculation from 8 AM.
            base_time = max(current_time, today_opd_start)

            estimated_turn = base_time + timedelta(
                minutes=patients_ahead * average_consultation_time
            )

        # Calculate estimated waiting time from now
        estimated_wait = max(
            0,
            int(
                (estimated_turn - current_time).total_seconds() / 60
            )
        )

        # Recommended arrival is 10 minutes before the turn
        recommended_arrival = estimated_turn - timedelta(
            minutes=arrival_buffer
        )

        # Never recommend arriving before OPD opens
        if recommended_arrival < today_opd_start:
            recommended_arrival = today_opd_start

        # Convert to readable format
        estimated_turn_time = estimated_turn.strftime("%I:%M %p")
        recommended_arrival_time = recommended_arrival.strftime(
            "%I:%M %p"
        )

    connection.close()

    return render_template(
    "queue.html",
    token_number=token_number,
    patient_name=patient_name,
    patient_age=patient_age,
    department_name=department_name,
    status=status,
    now_serving=now_serving,
    patients_ahead=patients_ahead,
    estimated_wait=estimated_wait,
    estimated_turn_time=estimated_turn_time,
    recommended_arrival_time=recommended_arrival_time
)


if __name__ == "__main__":
    app.run(debug=True)
