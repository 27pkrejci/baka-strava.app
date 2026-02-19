import logging
import scbc.scheduler as s

logging.basicConfig(level=logging.INFO)
print("Starting full schedule update...")
s._update_all_schedules()
print("Update finished.")
