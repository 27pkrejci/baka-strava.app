from strava_cz import StravaCZ
import json

# 1. Setup credentials (copied from your main script)
strava = StravaCZ(username="antonin.krejci", password="Ton224551", canteen_number="6627")

print("--- Starting Fetch ---")

try:
    # 2. Get the menu
    menu = strava.get_menu(include_soup=True)
    
    # 3. Print the summary
    print(f"✅ Fetched {len(menu)} days of menu data.")
    print("-" * 20)

    # 4. Print each day in a readable way
    for day in menu:
        # We use json.dumps just to make the print look 'pretty' and indented
        print(json.dumps(day, indent=2, ensure_ascii=False))
        print("-" * 20)

except Exception as e:
    print(f"❌ An error occurred: {e}")