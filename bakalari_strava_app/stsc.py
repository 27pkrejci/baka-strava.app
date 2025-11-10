from strava_cz import StravaCZ
import psycopg2
import json

conn = psycopg2.connect(
    dbname="school_dashboard",
    user="postgres",
    password="dat224551",
    host="db",
    port="5432"
)
cur = conn.cursor()

cur.execute("TRUNCATE TABLE lunch RESTART IDENTITY;")

strava = StravaCZ(username="antonin.krejci", password="Ton224551", canteen_number="6627")
menu = strava.get_menu()

for day_data in menu:
    date = day_data['date']
    for meal in day_data['meals']:
        cur.execute("""
            INSERT INTO lunch (date, meal_type, name, allergens, ordered)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            date,
            meal['type'],
            meal['name'],
            json.dumps(meal['alergens']),
            meal['ordered']
        ))

conn.commit()
cur.close()
conn.close()

print("✅ Lunch menu data saved successfully!")
