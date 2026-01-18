"""
Scheduler module for automated schedule updates.

Runs on a schedule (every hour by default) to fetch and update all class schedules
in the database.
"""

import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .class_list import fetch_classes_from_school
from .cli import upload_schedule


logger = logging.getLogger(__name__)


_scheduler = None


def schedule_update_task(hours: int = 1):
    """
    Start the background scheduler to update all class schedules periodically.
    
    Args:
        hours: Update interval in hours (default: 1)
    """
    global _scheduler
    
    if _scheduler is not None:
        logger.warning("Scheduler already running, not starting a second one")
        return _scheduler
    
    _scheduler = BackgroundScheduler()

    _scheduler.add_job(
        _update_all_schedules,
        trigger=IntervalTrigger(hours=hours),
        id='schedule_update',
        name='Update all class schedules',
        replace_existing=True,
        max_instances=1
    )
    
    _scheduler.start()
    logger.info(f"✅ Schedule updater started (runs every {hours} hour{'s' if hours > 1 else ''})")
    
    return _scheduler


def stop_scheduler():
    """Stop the background scheduler."""
    global _scheduler
    
    if _scheduler is not None:
        _scheduler.shutdown()
        _scheduler = None
        logger.info("✅ Schedule updater stopped")


def _update_all_schedules():
    """
    Fetch all classes from the school website and update the database.
    This function runs in the background on a schedule.
    """
    logger.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting automatic schedule update...")
    
    try:
        classes = fetch_classes_from_school()
        logger.info(f"Found {len(classes)} classes to update")
        
        success_count = 0
        error_count = 0
        
        for cls in classes:
            class_identifier = cls['name']
            code = cls['code']
            
            try:
                logger.debug(f"Updating schedule for {class_identifier} (code: {code})...")
                inserted = upload_schedule(code, class_identifier, confirm=False, dry_run=False)
                logger.info(f"✅ Updated {class_identifier}: {inserted} entries")
                success_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to update {class_identifier}: {e}")
                error_count += 1
        
        logger.info(f"Schedule update completed: {success_count} succeeded, {error_count} failed")
    
    except Exception as e:
        logger.error(f"❌ Failed to fetch class list: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Starting scheduler in test mode (updates every 1 minute)...")
    scheduler = schedule_update_task(hours=1/60)
    
    try:
        import time
        print("Scheduler running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
        stop_scheduler()
        print("Done.")
