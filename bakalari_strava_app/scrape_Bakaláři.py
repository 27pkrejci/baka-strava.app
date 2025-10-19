import requests
from bs4 import BeautifulSoup
import psycopg2

BASE_URL = "https://www.dgkralupy.cz/BakaFiles/rozvrh"
CLASS_FILE = "truy.htm"
TABLE_NAME = 'rozvrh_3_P'

DB_CONFIG = {
    "dbname": "school_dashboard",
    "user": "postgres",
    "password": "dat224551",
    "host": "localhost",
    "port": "1325"
}

def fetch_schedule():
    url = f"{BASE_URL}/{CLASS_FILE}"
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")

    schedule = []
    current_day = None
    current_time = None

    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if not cells:
            continue

        cell_texts = [td.get_text(strip=True) for td in cells if td.get_text(strip=True)]
        for text in cell_texts:
            if text in ["Po", "Út", "St", "Čt", "Pá"]:
                current_day = text
                continue
            if "-" in text:
                current_time = text
                continue
            if len(text) < 2:
                continue

            subject = teacher = class_group = room = ""
            import re
            m = re.match(r"([A-Za-zŠČŘŽÝÁÍÉ]+)\((.*?)\)([A-Za-z]+)?\((\d+)\)?", text)
            if m:
                subject, class_group, teacher, room = m.groups()
                class_group = f"({class_group})" if class_group else ""
                room = f"({room})" if room else ""
            else:
                subject = text

            schedule.append({
                "day": current_day if current_day else "Unknown Day",
                "time_slot": current_time if current_time else "",
                "subject": subject,
                "teacher": teacher,
                "class_group": class_group,
                "room": room
            })
    print(f"Fetched {len(schedule)} entries.")
    return schedule

def create_table():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            Rid SERIAL PRIMARY KEY,
            day TEXT,
            time_slot TEXT,
            subject TEXT,
            teacher TEXT,
            class_group TEXT,
            room TEXT
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def insert_schedule_to_db(schedule):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    insert_query = f"""
        INSERT INTO "{TABLE_NAME}" (day, time_slot, subject, teacher, class_group, room)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    values = [(entry["day"], entry["time_slot"], entry["subject"], entry["teacher"], entry["class_group"], entry["room"]) for entry in schedule]
    cursor.executemany(insert_query, values)
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Inserted {len(values)} entries into {TABLE_NAME}.")

if __name__ == "__main__":
    create_table()
    schedule = fetch_schedule()
    insert_schedule_to_db(schedule)