from datetime import datetime, timedelta

# Time slots mapping
TIME_SLOT_ORDER = {
    "8:00- 8:45": 1, "8:55- 9:40": 2, "10:00-10:45": 3, "10:55-11:40": 4,
    "11:50-12:35": 5, "12:45-13:30": 6, "13:35-14:20": 7, "14:25-15:10": 8,
    "15:15-16:00": 9
}

# Day mapping - English to Czech short names
DAY_NAMES_SHORT = {
    'Monday': 'Po',
    'Tuesday': 'Út',
    'Wednesday': 'St',
    'Thursday': 'Čt',
    'Friday': 'Pá'
}

# Database day names (what's stored in DB)
DB_DAY_NAMES = {
    'Monday': 'Po',
    'Tuesday': 'Ut',
    'Wednesday': 'St',
    'Thursday': 'Ct',
    'Friday': 'Pa'
}


class WeekScheduleRepository:
    """Responsible for fetching and organizing week schedule data."""
    
    def __init__(self, db_connection_func):
        self.db_connection_func = db_connection_func
    
    def get_week_schedule(self):
        """
        Fetch the week schedule (Monday-Friday) organized by day and time slot.
        
        Returns:
            dict: Schedule organized as {
                'Monday': {
                    'day_short': 'Po',
                    'lessons': {
                        '8:00- 8:45': [
                            {'group': 'Group', 'room': '123', 'subject': 'Math', 'teacher': 'Prof X'},
                            ...
                        ],
                        ...
                    }
                },
                ...
            }
        """
        try:
            conn = self.db_connection_func()
            cur = conn.cursor()
            
            # Fetch all lessons for all weekdays (including week attribute: S, L, or NULL)
            query = """
                SELECT day, time_slot, subject, "group", teacher, room, week
                FROM timetable_3p
                WHERE day IN ('Po', 'Ut', 'St', 'Ct', 'Pa')
                ORDER BY day, 
                         CASE time_slot
                             WHEN '8:00- 8:45' THEN 1
                             WHEN '8:55- 9:40' THEN 2
                             WHEN '10:00-10:45' THEN 3
                             WHEN '10:55-11:40' THEN 4
                             WHEN '11:50-12:35' THEN 5
                             WHEN '12:45-13:30' THEN 6
                             WHEN '13:35-14:20' THEN 7
                             WHEN '14:25-15:10' THEN 8
                             WHEN '15:15-16:00' THEN 9
                             ELSE 99
                         END
            """
            
            cur.execute(query)
            rows = cur.fetchall()
            cur.close()
            conn.close()
            
            # Organize data by day and time slot
            week_schedule = self._organize_schedule(rows)
            
            return week_schedule
        
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")
    
    def _organize_schedule(self, rows):
        """
        Organize raw database rows into a structured dict.
        
        Returns:
            dict: Organized schedule with days as keys and lessons grouped by time slot
        """
        # Initialize structure for all weekdays
        days_order = ['Po', 'Ut', 'St', 'Ct', 'Pa']
        day_to_english = {
            'Po': 'Monday',
            'Ut': 'Tuesday',
            'St': 'Wednesday',
            'Ct': 'Thursday',
            'Pa': 'Friday'
        }
        
        schedule = {}
        for db_day in days_order:
            english_day = day_to_english[db_day]
            schedule[english_day] = {
                'day_short': db_day,
                'lessons': {slot: [] for slot in TIME_SLOT_ORDER.keys()}
            }
        
        # Populate with actual data
        for row in rows:
            db_day, time_slot, subject, group, teacher, room, week = row
            english_day = day_to_english.get(db_day)
            
            if english_day and english_day in schedule and time_slot in schedule[english_day]['lessons']:
                schedule[english_day]['lessons'][time_slot].append({
                    'group': group or '',
                    'room': room or '',
                    'subject': subject or '',
                    'teacher': teacher or '',
                    'week': week or ''  # S, L, or empty string
                })
        
        return schedule


def get_week_schedule(db_connection_func):
    """Helper function to get week schedule."""
    repo = WeekScheduleRepository(db_connection_func)
    return repo.get_week_schedule()
