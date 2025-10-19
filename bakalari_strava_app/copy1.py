import requests
from bs4 import BeautifulSoup
import sqlite3

# ---------------------------
# Database setup
# ---------------------------
conn = sqlite3.connect("schedules.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS schedules (
    rid INTEGER PRIMARY KEY AUTOINCREMENT,
    class_name TEXT,
    day TEXT,
    period INTEGER,
    subject TEXT
)
""")
conn.commit()

# ---------------------------
# Fetch URL
# ---------------------------
end_url = input("Enter the end part of the schedule URL: ").strip()
full_url = f"https://www.dgkralupy.cz/BakaFiles/rozvrh/{end_url}"
print(f"Fetching schedule from: {full_url}")

response = requests.get(full_url)
if response.status_code != 200:
    raise Exception(f"Failed to fetch schedule. Status code: {response.status_code}")

soup = BeautifulSoup(response.text, "html.parser")
print("Schedule fetched successfully!")

# ---------------------------
# Extract class name
# ---------------------------
rows = soup.find_all("tr")
if len(rows) < 2:
    raise Exception("Unexpected schedule format: not enough rows for class name.")

class_tr = rows[1]
class_span = class_tr.find("span", class_="textlargebold_1")
if not class_span:
    raise Exception("Could not find class name span.")

class_name = class_span.get_text(strip=True)
print(f"\nSchedule is for class: {class_name}")

# ---------------------------
# Check DB for existing schedule
# ---------------------------
cursor.execute("SELECT COUNT(*) FROM schedules WHERE class_name = ?", (class_name,))
exists = cursor.fetchone()[0] > 0

if exists:
    choice = input(f"Class schedule already saved in database for {class_name}. Replace the old one? (yes/no): ").strip().lower()
    if choice != "yes":
        print("Aborting.")
        exit()
    else:
        cursor.execute("DELETE FROM schedules WHERE class_name = ?", (class_name,))
        conn.commit()
        print(f"Old schedule for {class_name} deleted.")
else:
    choice = input(f"No saved schedule in database for {class_name}. Create new one? (yes/no): ").strip().lower()
    if choice != "yes":
        print("Aborting.")
        exit()

# ---------------------------
# Parse schedule table
# ---------------------------
days_map = ["Po", "Út", "St", "Čt", "Pá"]
schedule = {day: [] for day in days_map}

# Find table with class schedule
table = soup.find("table", class_="rozvrh")
if not table:
    raise Exception("Could not find schedule table.")

table_rows = table.find_all("tr")

# Keep track of rowspan for merged cells
rowspan_map = {day: [] for day in days_map}

for row_idx, row in enumerate(table_rows):
    cols = row.find_all("td")
    if not cols:
        continue

    # Each row corresponds to a row in the visual table
    day_idx = row_idx % len(days_map)  # simple approximation, adjust later if needed
    day = days_map[day_idx]

    col_idx = 0
    while col_idx < len(cols):
        cell = cols[col_idx]
        # Determine rowspan
        rowspan = int(cell.get("rowspan", 1))
        subject_texts = []

        # Sometimes multiple subjects in same cell (split class)
        inner_subjects = cell.find_all("div")
        if inner_subjects:
            for s in inner_subjects:
                subject_texts.append(s.get_text(strip=True))
        else:
            subject_texts.append(cell.get_text(strip=True))

        # Add each subject separately
        for i in range(rowspan):
            for subject in subject_texts:
                schedule[day].append(subject if subject else "-- o --")

        col_idx += 1

# ---------------------------
# Show debug schedule
# ---------------------------
print("\nDEBUG: Full parsed schedule:\n")
for day, subjects in schedule.items():
    print(f"{day}:")
    for idx, subj in enumerate(subjects, start=1):
        print(f"  {idx}: {subj}")
    print()

# ---------------------------
# Insert into database
# ---------------------------
rid_counter = 1
for day, subjects in schedule.items():
    for period_idx, subject in enumerate(subjects, start=1):
        cursor.execute(
            "INSERT INTO schedules (rid, class_name, day, period, subject) VALUES (?, ?, ?, ?, ?)",
            (rid_counter, class_name, day, period_idx, subject)
        )
        rid_counter += 1

conn.commit()
print(f"Schedule for {class_name} saved successfully!")

conn.close()
