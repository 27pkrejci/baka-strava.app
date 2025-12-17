# timetable_api.py - Refactored for SRP
from datetime import datetime, time
import json

# Define time slots with their order in one place to avoid duplication
TIME_SLOT_ORDER = {
    "8:00- 8:45": 1, "8:55- 9:40": 2, "10:00-10:45": 3, "10:55-11:40": 4,
    "11:50-12:35": 5, "12:45-13:30": 6, "13:35-14:20": 7, "14:25-15:10": 8,
    "15:15-16:00": 9, "16:25-17:10": 10
}

# Derive TIME_SLOTS from the order dictionary
TIME_SLOTS = list(TIME_SLOT_ORDER.keys())

# Mapování anglických dnů na české
DAYS_MAP = {
    'Monday': 'Po', 'Tuesday': 'Ut', 'Wednesday': 'St',
    'Thursday': 'Ct', 'Friday': 'Pa', 'Saturday': 'So', 'Sunday': 'Ne'
}

class TimeSlotParser:
    """Responsible for parsing and managing time slots."""
    
    @staticmethod
    def parse_time_slot(slot_str):
        """Převést časový slot (např. '8:00- 8:45') na časové objekty"""
        clean = slot_str.replace(" ", "")
        start_str, end_str = clean.split("-")
        
        start = datetime.strptime(start_str, "%H:%M").time()
        end = datetime.strptime(end_str, "%H:%M").time()
        
        return {
            'display': slot_str,
            'start': start,
            'end': end,
            'start_minutes': start.hour * 60 + start.minute,
            'end_minutes': end.hour * 60 + end.minute
        }
    
    @staticmethod
    def get_parsed_time_slots():
        """Return list of parsed time slots."""
        return [TimeSlotParser.parse_time_slot(slot) for slot in TIME_SLOTS]

class TimetableRepository:
    """Responsible for database operations related to timetable."""
    
    def __init__(self, db_connection_func):
        self.db_connection_func = db_connection_func
    
    def get_lessons_for_day(self, czech_day):
        """Fetch lessons for a given day from database."""
        try:
            conn = self.db_connection_func()
            cur = conn.cursor()
            
            # Generate ORDER BY clause dynamically from TIME_SLOT_ORDER
            order_cases = []
            for slot, order_num in TIME_SLOT_ORDER.items():
                order_cases.append(f"WHEN '{slot}' THEN {order_num}")
            order_by_clause = "CASE time_slot\n" + "\n".join(f"                    {case}" for case in order_cases) + "\n                    ELSE 99\n                END"
            
            query = f"""
                SELECT time_slot, subject, "group", teacher, room, week
                FROM timetable_3p 
                WHERE day = %s
                ORDER BY {order_by_clause}
            """
            
            cur.execute(query, (czech_day,))
            
            db_rows = cur.fetchall()
            cur.close()
            conn.close()
            
            return db_rows
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")
    
    def group_lessons_by_slot(self, db_rows):
        """Group lessons by time slot."""
        lessons_by_slot = {}
        for row in db_rows:
            time_slot = row[0]
            if time_slot not in lessons_by_slot:
                lessons_by_slot[time_slot] = []
            
            lessons_by_slot[time_slot].append({
                'subject': row[1] or '',
                'group': row[2] or '',
                'teacher': row[3] or '',
                'room': row[4] or '',
                'week': row[5]
            })
        return lessons_by_slot

class CurrentPeriodCalculator:
    """Responsible for calculating current period state."""
    
    def __init__(self, time_slots, lessons_by_slot):
        self.time_slots = time_slots
        self.lessons_by_slot = lessons_by_slot
    
    def find_slots(self, current_minutes):
        """Find previous, current, and next time slots."""
        previous_slot = None
        current_slot = None
        next_slot = None
        
        for i, slot in enumerate(self.time_slots):
            if current_minutes < slot['start_minutes']:
                next_slot = slot
                if i > 0:
                    previous_slot = self.time_slots[i-1]
                break
            elif slot['start_minutes'] <= current_minutes < slot['end_minutes']:
                current_slot = slot
                if i > 0:
                    previous_slot = self.time_slots[i-1]
                if i < len(self.time_slots) - 1:
                    next_slot = self.time_slots[i+1]
                break
            else:
                previous_slot = slot
        
        # After all lessons
        if not current_slot and not next_slot and self.time_slots:
            previous_slot = self.time_slots[-1]
        
        return previous_slot, current_slot, next_slot
    
    def get_lessons_for_slot(self, slot):
        """Get lessons for a specific slot."""
        if not slot or slot['display'] not in self.lessons_by_slot:
            return []
        return self.lessons_by_slot[slot['display']]
    
    def determine_state(self, current_slot, next_slot, current_minutes):
        """Determine the current state."""
        if current_slot:
            return "in_lesson"
        elif next_slot:
            return "break"
        else:
            return "after_school"

class ResponseFormatter:
    """Responsible for formatting the response."""
    
    @staticmethod
    def format_response(now, czech_day, english_day, current_time, current_minutes, 
                       previous_slot, current_slot, next_slot, calculator, state):
        """Format the complete response."""
        result = {
            "status": "success",
            "date": now.strftime("%Y-%m-%d"),
            "date_display": now.strftime("%d.%m.%Y"),
            "day": czech_day,
            "day_english": english_day,
            "current_time": current_time.strftime("%H:%M"),
            "current_minutes": current_minutes,
            "state": state,
            "previous": None,
            "current": None,
            "next": None
        }
        
        if current_slot:
            result["current"] = {
                "time_slot": current_slot['display'],
                "start_time": current_slot['start'].strftime("%H:%M"),
                "end_time": current_slot['end'].strftime("%H:%M"),
                "lessons": calculator.get_lessons_for_slot(current_slot),
                "minutes_remaining": current_slot['end_minutes'] - current_minutes
            }
        
        if previous_slot:
            result["previous"] = {
                "time_slot": previous_slot['display'],
                "start_time": previous_slot['start'].strftime("%H:%M"),
                "end_time": previous_slot['end'].strftime("%H:%M"),
                "lessons": calculator.get_lessons_for_slot(previous_slot)
            }
        
        if next_slot:
            result["next"] = {
                "time_slot": next_slot['display'],
                "start_time": next_slot['start'].strftime("%H:%M"),
                "end_time": next_slot['end'].strftime("%H:%M"),
                "lessons": calculator.get_lessons_for_slot(next_slot),
                "minutes_until": next_slot['start_minutes'] - current_minutes
            }
        
        return result

def find_current_period(db_connection_func):
    """
    Main function - finds previous, current and next period.
    Orchestrates the SRP classes.
    """
    print("=" * 50)
    print("🔄 TIMETABLE_API: START")
    
    now = datetime.now()
    current_time = now.time()
    current_minutes = current_time.hour * 60 + current_time.minute
    
    # Get day
    english_day = now.strftime("%A")
    czech_day = DAYS_MAP.get(english_day, english_day)
    
    print(f"📅 Den: {english_day} -> {czech_day}")
    print(f"⏰ Čas: {current_time} ({current_minutes} minut)")
    
    # Check weekend
    if english_day in ['Saturday', 'Sunday']:
        print("🎉 Je víkend!")
        return {
            "status": "weekend",
            "date": now.strftime("%Y-%m-%d"),
            "date_display": now.strftime("%d.%m.%Y"),
            "day": czech_day,
            "day_english": english_day,
            "current_time": current_time.strftime("%H:%M"),
            "current_minutes": current_minutes,
            "state": "weekend",
            "message": "Je víkend!",
            "previous": None,
            "current": None,
            "next": None
        }
    
    try:
        # Initialize components
        time_slot_parser = TimeSlotParser()
        time_slots = time_slot_parser.get_parsed_time_slots()
        
        repository = TimetableRepository(db_connection_func)
        db_rows = repository.get_lessons_for_day(czech_day)
        
        if not db_rows:
            print("📭 Dnes není rozvrh")
            return {
                "status": "success",
                "date": now.strftime("%Y-%m-%d"),
                "date_display": now.strftime("%d.%m.%Y"),
                "day": czech_day,
                "day_english": english_day,
                "current_time": current_time.strftime("%H:%M"),
                "current_minutes": current_minutes,
                "state": "no_schedule",
                "message": "Dnes není rozvrh",
                "previous": None,
                "current": None,
                "next": None
            }
        
        lessons_by_slot = repository.group_lessons_by_slot(db_rows)
        
        calculator = CurrentPeriodCalculator(time_slots, lessons_by_slot)
        previous_slot, current_slot, next_slot = calculator.find_slots(current_minutes)
        
        print(f"📍 Slot pozice: previous={previous_slot['display'] if previous_slot else 'None'}, "
              f"current={current_slot['display'] if current_slot else 'None'}, "
              f"next={next_slot['display'] if next_slot else 'None'}")
        
        state = calculator.determine_state(current_slot, next_slot, current_minutes)
        
        if current_slot:
            print(f"🏫 Ve výuce: {current_slot['display']}")
        elif next_slot:
            print(f"☕ Přestávka, další hodina za {next_slot['start_minutes'] - current_minutes} minut")
        else:
            print("🏁 Po škole")
        
        formatter = ResponseFormatter()
        result = formatter.format_response(now, czech_day, english_day, current_time, 
                                         current_minutes, previous_slot, current_slot, 
                                         next_slot, calculator, state)
        
    except Exception as e:
        print(f"❌ CHYBA: {e}")
        import traceback
        traceback.print_exc()
        
        result = {
            "status": "error",
            "message": f"Chyba: {str(e)}"
        }
    
    print("✅ TIMETABLE_API: KONEC")
    print("=" * 50)
    return result