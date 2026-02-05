from datetime import datetime, timedelta

# Mapping of Czech day names
CZECH_DAY_NAMES = {
    'Monday': 'Pondělí',
    'Tuesday': 'Úterý',
    'Wednesday': 'Středa',
    'Thursday': 'Čtvrtek',
    'Friday': 'Pátek',
    'Saturday': 'Sobota',
    'Sunday': 'Neděle'
}


class LunchRepository:
    """Responsible for database operations related to lunch data."""
    
    def __init__(self, db_connection_func):
        self.db_connection_func = db_connection_func
    
    def get_lunch_schedule(self, days=6):
        """
        Fetch lunch data for the next N days (today + next N-1 days).
        
        Args:
            days (int): Number of days to fetch (default 6)
        
        Returns:
            list: List of dicts with date, day_name, and meals organized by type
        """
        try:
            conn = self.db_connection_func()
            cur = conn.cursor()
            
            # Get today's date and calculate the range
            today = datetime.now().date()
            end_date = today + timedelta(days=days - 1)
            
            # Fetch all lunch data for the date range
            query = """
                SELECT date, meal_type, name 
                FROM lunch 
                WHERE date >= %s AND date <= %s
                ORDER BY date, meal_type
            """
            cur.execute(query, (today, end_date))
            rows = cur.fetchall()
            cur.close()
            conn.close()
            
            # Organize data by date
            lunch_by_date = {}
            for row in rows:
                date, meal_type, name = row
                if date not in lunch_by_date:
                    lunch_by_date[date] = {
                        'soup': None,
                        'first': None,
                        'second': None,
                        'doplněk': None
                    }
                
                # Categorize meal type
                mt = (meal_type or '').strip().lower()
                if 'pol' in mt or 'soup' in mt:
                    lunch_by_date[date]['soup'] = name
                elif 'dopln' in mt or 'dop' in mt:
                    lunch_by_date[date]['doplněk'] = name
                elif mt.startswith('1') or mt in ('1', 'first'):
                    lunch_by_date[date]['first'] = name
                elif mt.startswith('2') or mt in ('2', 'second'):
                    lunch_by_date[date]['second'] = name
                else:
                    # Fallback: check if '1' or '2' is in the string
                    if '1' in mt:
                        lunch_by_date[date]['first'] = name
                    elif '2' in mt:
                        lunch_by_date[date]['second'] = name
            
            # Build the response with dates, day names, and meals
            result = []
            for i in range(days):
                current_date = today + timedelta(days=i)
                day_of_week = current_date.strftime('%A')
                czech_day_name = CZECH_DAY_NAMES.get(day_of_week, day_of_week)
                
                # Format date as "DD.M." (e.g., "19.1.") in a platform-independent way
                formatted_date = f"{current_date.day}.{current_date.month}."
                
                meals = lunch_by_date.get(current_date, {
                    'soup': None,
                    'first': None,
                    'second': None,
                    'doplněk': None
                })
                
                result.append({
                    'date': str(current_date),
                    'formatted_date': formatted_date,
                    'day_name': czech_day_name,
                    'soup': meals.get('soup'),
                    'first': meals.get('first'),
                    'second': meals.get('second'),
                    'doplněk': meals.get('doplněk')
                })
            
            return result
        
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")


def get_lunch_schedule(db_connection_func, days=6):
    """Helper function to get lunch schedule."""
    repo = LunchRepository(db_connection_func)
    return repo.get_lunch_schedule(days)
