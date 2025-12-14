# timetable_api.py
from datetime import datetime, time
import json

# Časové sloty z tvého 3p.json
TIME_SLOTS = [
    "8:00- 8:45", "8:55- 9:40", "10:00-10:45", "10:55-11:40",
    "11:50-12:35", "12:45-13:30", "13:35-14:20", "14:25-15:10",
    "15:15-16:00", "16:25-17:10"
]

# Mapování anglických dnů na české
DAYS_MAP = {
    'Monday': 'Po', 'Tuesday': 'Ut', 'Wednesday': 'St',
    'Thursday': 'Ct', 'Friday': 'Pa', 'Saturday': 'So', 'Sunday': 'Ne'
}

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

def find_current_period(db_connection_func):
    """
    Hlavní funkce - najde předchozí, aktuální a příští hodinu
    
    Parametr: db_connection_func - funkce která vrátí připojení k DB
    """
    now = datetime.now()
    current_time = now.time()
    current_minutes = current_time.hour * 60 + current_time.minute
    
    # Získat dnešní den
    english_day = now.strftime("%A")  # 'Monday', 'Tuesday'...
    czech_day = DAYS_MAP.get(english_day, english_day)
    
    # Výsledek
    result = {
        "status": "success",
        "date": now.strftime("%Y-%m-%d"),
        "date_display": now.strftime("%d.%m.%Y"),
        "day": czech_day,
        "day_english": english_day,
        "current_time": current_time.strftime("%H:%M"),
        "current_minutes": current_minutes,
        "state": None,
        "previous": None,
        "current": None,
        "next": None
    }
    
    # 1. Kontrola víkendu
    if english_day in ['Saturday', 'Sunday']:
        result["status"] = "weekend"
        result["state"] = "weekend"
        result["message"] = "Je víkend!"
        return result
    
    # 2. Připravit časové sloty
    time_slots = [parse_time_slot(slot) for slot in TIME_SLOTS]
    
    # 3. Načíst rozvrh z databáze
    try:
        conn = db_connection_func()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT time_slot, subject, "group", teacher, room, week
            FROM timetable_3p 
            WHERE day = %s
            ORDER BY 
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
                    WHEN '16:25-17:10' THEN 10
                    ELSE 99
                END
        """, (czech_day,))
        
        db_rows = cur.fetchall()
        cur.close()
        conn.close()
        
        # Pokud dnes není rozvrh
        if not db_rows:
            result["state"] = "no_schedule"
            result["message"] = "Dnes není rozvrh"
            return result
        
        # 4. Seskupit předměty podle časových slotů
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
        
        # 5. Najít předchozí, aktuální a příští slot
        previous_slot = None
        current_slot = None
        next_slot = None
        
        for i, slot in enumerate(time_slots):
            # Jsme před začátkem tohoto slotu
            if current_minutes < slot['start_minutes']:
                next_slot = slot
                if i > 0:
                    previous_slot = time_slots[i-1]
                break
            
            # Jsme během tohoto slotu
            elif slot['start_minutes'] <= current_minutes < slot['end_minutes']:
                current_slot = slot
                if i > 0:
                    previous_slot = time_slots[i-1]
                if i < len(time_slots) - 1:
                    next_slot = time_slots[i+1]
                break
            
            # Jsme po tomto slotu
            else:
                previous_slot = slot
        
        # Jsme po všech hodinách
        if not current_slot and not next_slot and time_slots:
            previous_slot = time_slots[-1]
        
        # 6. Přidat předměty k nalezeným slotům
        def get_lessons_for_slot(slot):
            if not slot or slot['display'] not in lessons_by_slot:
                return []
            return lessons_by_slot[slot['display']]
        
        # 7. Určit stav
        if current_slot:
            result["state"] = "in_lesson"
            result["current"] = {
                "time_slot": current_slot['display'],
                "start_time": current_slot['start'].strftime("%H:%M"),
                "end_time": current_slot['end'].strftime("%H:%M"),
                "lessons": get_lessons_for_slot(current_slot),
                "minutes_remaining": current_slot['end_minutes'] - current_minutes
            }
        elif next_slot:
            result["state"] = "break"
        else:
            result["state"] = "after_school"
        
        # 8. Předchozí hodina
        if previous_slot:
            result["previous"] = {
                "time_slot": previous_slot['display'],
                "start_time": previous_slot['start'].strftime("%H:%M"),
                "end_time": previous_slot['end'].strftime("%H:%M"),
                "lessons": get_lessons_for_slot(previous_slot)
            }
        
        # 9. Příští hodina
        if next_slot:
            result["next"] = {
                "time_slot": next_slot['display'],
                "start_time": next_slot['start'].strftime("%H:%M"),
                "end_time": next_slot['end'].strftime("%H:%M"),
                "lessons": get_lessons_for_slot(next_slot),
                "minutes_until": next_slot['start_minutes'] - current_minutes
            }
        
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"Chyba databáze: {str(e)}"
    
    return result