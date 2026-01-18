from strava_cz import StravaCZ
import psycopg2
import json
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from scbc.config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT

logger = logging.getLogger(__name__)

# Global scheduler instance
_lunch_scheduler = None


def _connect_db():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=int(DB_PORT)
    )


def main():
    conn = _connect_db()
    cur = conn.cursor()

    cur.execute("TRUNCATE TABLE lunch RESTART IDENTITY;")

    # NOTE: StravaCZ credentials are stored here in legacy code. Keep them safe.
    strava = StravaCZ(username="antonin.krejci", password="Ton224551", canteen_number="6627")
    menu = strava.get_menu(include_soup=True)  # Include soups in the menu

    for day_data in menu:
        date = day_data['date']
        for meal in day_data.get('meals', []):
            allergens = meal.get('alergens') or meal.get('allergens')
            cur.execute("""
                INSERT INTO lunch (date, meal_type, name, allergens, ordered)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                date,
                meal.get('type'),
                meal.get('name'),
                json.dumps(allergens) if allergens is not None else None,
                meal.get('ordered', False)
            ))

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Lunch menu data saved successfully!")


def schedule_lunch_updates(hour: int = 6, minute: int = 0):
    """
    Start the background scheduler to update lunch menu daily.
    
    Args:
        hour: Hour of day to run (0-23, default 6 = 6 AM)
        minute: Minute of hour (0-59, default 0)
    """
    global _lunch_scheduler
    
    if _lunch_scheduler is not None:
        logger.warning("Lunch scheduler already running, not starting a second one")
        return _lunch_scheduler
    
    _lunch_scheduler = BackgroundScheduler()
    
    # Add the update job to run daily at specified time
    _lunch_scheduler.add_job(
        main,
        trigger=CronTrigger(hour=hour, minute=minute),
        id='lunch_update',
        name='Update lunch menu daily',
        replace_existing=True,
        max_instances=1
    )
    
    _lunch_scheduler.start()
    logger.info(f"✅ Lunch menu updater started (runs daily at {hour:02d}:{minute:02d})")
    
    return _lunch_scheduler


def stop_lunch_scheduler():
    """Stop the background scheduler."""
    global _lunch_scheduler
    
    if _lunch_scheduler is not None:
        _lunch_scheduler.shutdown()
        _lunch_scheduler = None
        logger.info("✅ Lunch menu updater stopped")


if __name__ == '__main__':
    main()
    main()
