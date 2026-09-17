import sqlite3


connection = sqlite3.connect("database/careflow.db")

cursor = connection.cursor()

cursor.execute("SELECT * FROM departments")

departments = cursor.fetchall()

for department in departments:
    print(department)

connection.close()