import csv
import psycopg2

# Connect to PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    port=1325,              # your port
    database="school_dashboard",
    user="postgres",        # your username
    password="dat224551" # your password
)
cur = conn.cursor()

# Open CSV and insert rows
with open('schedule.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        cur.execute("""
            INSERT INTO classes (day, period, subject, teacher, room)
            VALUES (%s, %s, %s, %s, %s)
        """, (row['day'], row['period'], row['subject'], row['teacher'], row['room']))

conn.commit()
cur.close()
conn.close()
print("Schedule loaded successfully!")
