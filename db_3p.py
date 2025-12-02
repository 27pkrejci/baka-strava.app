import json
import psycopg2

# ====== DB CONFIG ======
DB_HOST = "localhost"
DB_NAME = "school_dashboard"
DB_USER = "postgres"
DB_PASSWORD = "dat224551"
DB_PORT = "1325"


def main():
    # Load JSON
    with open("3p.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    entries = data["entries"]

    # Connect to PostgreSQL
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cur = conn.cursor()

    # Create table
    cur.execute("""
        DROP TABLE IF EXISTS timetable_3p;

        CREATE TABLE timetable_3p (
            rid         INTEGER PRIMARY KEY,
            day         VARCHAR(5),
            time_slot   VARCHAR(20),
            subject     VARCHAR(20),
            "group"     VARCHAR(20),
            teacher     VARCHAR(20),
            room        VARCHAR(10)
        );
    """)

    # Insert rows
    for e in entries:
        cur.execute("""
            INSERT INTO timetable_3p (rid, day, time_slot, subject, "group", teacher, room)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """, (
            e["rid"],
            e["day"],
            e["time_slot"],
            e["subject"],
            e["group"],
            e["teacher"],
            e["room"]
        ))

    # Commit and close
    conn.commit()
    cur.close()
    conn.close()

    print("✔ Successfully imported 3p.json into timetable_3p!")


if __name__ == "__main__":
    main()