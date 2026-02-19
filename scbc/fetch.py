import os
from bs4 import BeautifulSoup
from .parser import parse_schedule


def fetch_schedule_from_file(file_path):
    """
    Fetch schedule HTML from a local file (for testing).
    Extract class name, time slots, and raw rows.
    Returns raw schedule dict.
    """
    if not os.path.exists(file_path):
        raise Exception(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")

    tables = soup.find_all("table")
    if len(tables) < 2:
        raise Exception("Could not find the schedule table.")
    schedule_table = tables[1]

    rows = schedule_table.find_all("tr")
    if len(rows) < 4:
        raise Exception("Not enough rows in schedule table.")

    class_tr = rows[1]
    class_span = class_tr.find("span", class_="textlargebold_1")
    if not class_span:
        raise Exception("Could not find class name span.")
    class_name = class_span.get_text(strip=True)

    print(f"\nSchedule is for class: {class_name}")

    time_slot_tr = rows[2]
    time_slots = []
    for td in time_slot_tr.find_all("td")[1:-1]:
        time_span = td.find("span", class_="textsmall_1")
        if time_span:
            time_text = time_span.get_text(strip=True)
            if time_text:
                time_slots.append(time_text)

    schedule_rows = []
    for tr in rows[3:-1]:
        td_list = []
        for td in tr.find_all("td"):
            cell_text = td.get_text(" ", strip=True)
            rowspan = int(td.get("rowspan", 1))
            td_list.append({"text": cell_text, "rowspan": rowspan, "elem": td})
        schedule_rows.append(td_list)

    print("\n===== DEBUG: Fetched raw schedule =====")
    print(f"Class Name: {class_name}")
    print(f"Time Slots: {time_slots}")
    print(f"Number of schedule rows: {len(schedule_rows)}")
    print("===== END DEBUG =====\n")

    return {
        "class_name": class_name,
        "time_slots": time_slots,
        "rows": schedule_rows
    }


def fetch_schedule_from_network(url_code):
    """
    Fetch schedule HTML from a live URL (for production).
    Same logic as fetch_schedule_from_file but fetches via network.
    url_code: 4-letter code for the schedule (e.g., 'truk' for 7.G)
    """
    import requests

    BASE_URL = "https://www.dgkralupy.cz/BakaFiles/rozvrh/"
    url = f"{BASE_URL}{url_code}.htm"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch page: {response.status_code}")
    
    response.encoding = 'windows-1250'
    soup = BeautifulSoup(response.text, "html.parser")

    tables = soup.find_all("table")
    if len(tables) < 2:
        raise Exception("Could not find the schedule table.")
    schedule_table = tables[1]

    rows = schedule_table.find_all("tr")
    if len(rows) < 4:
        raise Exception("Not enough rows in schedule table.")

    class_tr = rows[1]
    class_span = class_tr.find("span", class_="textlargebold_1")
    if not class_span:
        raise Exception("Could not find class name span.")
    class_name = class_span.get_text(strip=True)

    print(f"\nSchedule is for class: {class_name}")

    time_slot_tr = rows[2]
    time_slots = []
    for td in time_slot_tr.find_all("td")[1:-1]:
        time_span = td.find("span", class_="textsmall_1")
        if time_span:
            time_text = time_span.get_text(strip=True)
            if time_text:
                time_slots.append(time_text)

    schedule_rows = []
    for tr in rows[3:-1]:
        td_list = []
        for td in tr.find_all("td"):
            cell_text = td.get_text(" ", strip=True)
            rowspan = int(td.get("rowspan", 1))
            # include the original element so that parser can inspect spans
            td_list.append({"text": cell_text, "rowspan": rowspan, "elem": td})
        schedule_rows.append(td_list)

    print("\n===== DEBUG: Fetched raw schedule =====")
    print(f"Class Name: {class_name}")
    print(f"Time Slots: {time_slots}")
    print(f"Number of schedule rows: {len(schedule_rows)}")
    print("===== END DEBUG =====\n")

    return {
        "class_name": class_name,
        "time_slots": time_slots,
        "rows": schedule_rows
    }
