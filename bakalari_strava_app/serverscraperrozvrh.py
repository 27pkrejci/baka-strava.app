# serverscraperrozvrh.py
"""
Server scraper for Bakalari schedule.
Step 1: Fetch schedule for a class, show debug data, and confirm with the user
before inserting/replacing in database.
"""

import requests
from bs4 import BeautifulSoup
import psycopg2

# ====== DB CONFIG ======
DB_HOST = "localhost"
DB_NAME = "school_dashboard"
DB_USER = "postgres"
DB_PASSWORD = "dat224551"
DB_PORT = "1325"

def fetch_schedule(url_end):
    """
    Fetch schedule HTML, extract class name, time slots, and raw rows.
    Checks database if schedule exists for this class.
    Returns raw schedule dict.
    """
    BASE_URL = "https://www.dgkralupy.cz/BakaFiles/rozvrh/"
    url = f"{BASE_URL}{url_end}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch page: {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")

    # ====== Select the second table (actual schedule) ======
    tables = soup.find_all("table")
    if len(tables) < 2:
        raise Exception("Could not find the schedule table.")
    schedule_table = tables[1]

    rows = schedule_table.find_all("tr")
    if len(rows) < 4:
        raise Exception("Not enough rows in schedule table.")

    # ====== Extract class name ======
    class_tr = rows[1]
    class_span = class_tr.find("span", class_="textlargebold_1")
    if not class_span:
        raise Exception("Could not find class name span.")
    class_name = class_span.get_text(strip=True)

    print(f"\nSchedule is for class: {class_name}")

    # ====== Connect to DB to check if schedule exists ======
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )
    cur = conn.cursor()

    # Try to check if table exists first
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'schedules'
        )
    """)
    table_exists = cur.fetchone()[0]

    schedule_exists = False
    if table_exists:
        cur.execute("SELECT COUNT(*) FROM schedules WHERE class_name = %s", (class_name,))
        schedule_exists = cur.fetchone()[0] > 0

    # ====== Ask user what to do ======
    if schedule_exists:
        choice = input(f"Schedule already exists for {class_name}. Replace it? (yes/no): ").strip().lower()
        if choice != "yes":
            print("Keeping existing schedule. Exiting.")
            exit()
    else:
        choice = input(f"No schedule exists for {class_name}. Create new? (yes/no): ").strip().lower()
        if choice != "yes":
            print("Not creating schedule. Exiting.")
            exit()

    # ====== Time slots from third TR ======
    time_slot_tr = rows[2]
    time_slots = [td.get_text(strip=True) for td in time_slot_tr.find_all("td")[1:-1] if td.get_text(strip=True)]

    # ====== Collect schedule rows (skip first 3 and last row) ======
    schedule_rows = []
    for tr in rows[3:-1]:
        td_list = []
        for td in tr.find_all("td"):
            cell_text = td.get_text(strip=True)
            rowspan = int(td.get("rowspan", 1))
            td_list.append({"text": cell_text, "rowspan": rowspan})
        schedule_rows.append(td_list)

    # ====== DEBUG OUTPUT ======
    print("\n===== DEBUG: Fetched raw schedule =====")
    print(f"Time Slots: {time_slots}")
    print(f"Number of schedule rows: {len(schedule_rows)}")
    for i, row in enumerate(schedule_rows[:5]):
        print(f"Row {i+1}: {row}")
    print("===== END DEBUG =====\n")

    cur.close()
    conn.close()

    return {
        "class_name": class_name,
        "time_slots": time_slots,
        "rows": schedule_rows
    }

def sep_schedule(raw_schedule):
    """
    Convert raw_schedule (dict from fetch_schedule) into structured schedule ready for DB.
    Implements virtual table per day to handle rowspan and split classes.
    """
    time_slots_raw = raw_schedule["time_slots"]
    # Clean time slots: remove leading numbers
    time_slots = [ts.split(' ', 1)[-1].strip() for ts in time_slots_raw]

    rows_list = raw_schedule["rows"]
    day_names = ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"]

    structured_schedule = []
    rid = 1
    current_day = None

    VIRTUAL_BOXES = 10  # number of boxes per day
    MAX_ROWSPAN = 6     # maximum rowspan

    # Virtual grid for the current day
    day_grid = [0] * VIRTUAL_BOXES

    for row in rows_list:
        used_boxes_this_row = [False] * VIRTUAL_BOXES
        col_idx = 0

        # Detect if this row contains day info
        second_td_text = row[1]["text"].strip()
        if second_td_text in day_names:
            current_day = second_td_text
            day_grid = [0] * VIRTUAL_BOXES  # reset the virtual grid
            col_idx += 1  # move past day column

        while col_idx < len(row):
            if col_idx == 0 or col_idx == 1 or col_idx == len(row) - 1:
                col_idx += 1
                continue  # skip spacing columns

            cell = row[col_idx]
            cell_text = cell["text"].strip()
            rowspan = cell.get("rowspan", 1)

            if not cell_text or cell_text in ["-- o --", "-- TH --"]:
                col_idx += 1
                continue

            # Find first available box in virtual grid not used in this row
            for box_idx, box_value in enumerate(day_grid):
                if not used_boxes_this_row[box_idx] and box_value < MAX_ROWSPAN:
                    break
            else:
                # fallback if all boxes are used, pick the first one
                box_idx = 0

            # Assign time slot based on box index
            ts_idx = box_idx if box_idx < len(time_slots) else len(time_slots)-1
            time_slot = time_slots[ts_idx]

            structured_schedule.append({
                "rid": rid,
                "day": current_day,
                "time_slot": time_slot,
                "subject": cell_text
            })
            rid += 1

            # Update virtual grid and mark box as used for this row
            day_grid[box_idx] += rowspan
            if day_grid[box_idx] > MAX_ROWSPAN:
                day_grid[box_idx] = MAX_ROWSPAN
            used_boxes_this_row[box_idx] = True

            col_idx += 1

    print(f"Processed {len(structured_schedule)} entries in sep_schedule.")
    return structured_schedule

def main():
    url_end = input("Enter the end of the schedule URL (e.g., 'truk.htm'): ").strip()
    raw_schedule = fetch_schedule(url_end)
    structured_schedule = sep_schedule(raw_schedule)

    print("\n=== FIRST 25 STRUCTURED ROWS ===")
    for row in structured_schedule[:25]:
        print(row)
    print(f"\nTotal entries ready for DB insertion: {len(structured_schedule)}")

if __name__ == "__main__":
    main()