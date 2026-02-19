from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import psycopg2
import logging
import json

from scbc.config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT
from scbc.scheduler import schedule_update_task, stop_scheduler
from stsc import schedule_lunch_updates, stop_lunch_scheduler
from timetable_api import find_current_period
from lunch_api import get_lunch_schedule


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))


class Lunch(db.Model):
    __tablename__ = 'lunch'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    meal_type = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    allergens = db.Column(db.String)
    ordered = db.Column(db.Boolean)

class Schedule(db.Model):
    __tablename__ = 'timetable_3p'
    rid = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String, nullable=False)
    time_slot = db.Column(db.String, nullable=False)
    subject = db.Column(db.String, nullable=False)
    group = db.Column(db.String, nullable=False)
    week = db.Column(db.String, nullable=True)
    teacher = db.Column(db.String, nullable=False)
    room = db.Column(db.String, nullable=False)

with app.app_context():
    db.create_all()
    print("✅ Database tables created!")


@app.before_request
def initialize_database():
    # Only run once
    if not hasattr(app, 'initialized'):
        app.initialized = True
        # Start the background schedulers for automatic updates
        try:
            schedule_update_task(hours=1)  # Update schedules every hour
            logger.info("✅ Schedule updater initialized")
        except Exception as e:
            logger.error(f"Failed to initialize schedule scheduler: {e}")
        
        try:
            schedule_lunch_updates(hour=6, minute=0)  # Update lunch menu daily at 6 AM
            logger.info("✅ Lunch menu updater initialized")
        except Exception as e:
            logger.error(f"Failed to initialize lunch scheduler: {e}")


# Database connection function
def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/lunch')
def lunch():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, date, meal_type, name, allergens, ordered FROM lunch ORDER BY id;")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        output = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Lunch Menu</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                h2 { color: #333; }
                table { border-collapse: collapse; width: 80%; }
                th, td { border: 1px solid #999; padding: 8px; text-align: left; }
                th { background-color: #eee; }
            </style>
        </head>
        <body>
            <h2>Lunch Menu</h2>
            <table>
                <tr>
                    <th>ID</th>
                    <th>Date</th>
                    <th>Meal Type</th>
                    <th>Name</th>
                    <th>Allergens</th>
                    <th>Ordered</th>
                </tr>
        """

        if rows:
            for id, date, meal_type, name, allergens, ordered in rows:
                output += f"<tr><td>{id}</td><td>{date}</td><td>{meal_type}</td><td>{name}</td><td>{allergens}</td><td>{ordered}</td></tr>"
        else:
            output += "<tr><td colspan='6'>No lunch data found.</td></tr>"

        output += "</table></body></html>"

        return output

    except Exception as e:
        return f"<p>Error fetching lunch menu: {e}</p>"


@app.route('/schedule')
def schedule():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT day, time_slot, subject, "group", week, teacher, room FROM timetable_3p ORDER BY day, time_slot;')
        rows = cur.fetchall()
        cur.close()
        conn.close()

        output = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Class Schedule</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                h2 { color: #333; }
                table { border-collapse: collapse; width: 80%; }
                th, td { border: 1px solid #999; padding: 8px; text-align: left; }
                th { background-color: #eee; }
            </style>
        </head>
        <body>
            <h2>Class Schedule</h2>
            <table>
                <tr>
                    <th>Day</th>
                    <th>Time_slot</th>
                    <th>Subject</th>
                    <th>Group</th>
                    <th>Week</th>
                    <th>Teacher</th>
                    <th>Room</th>
                </tr>
        """

        if rows:
            for day, time_slot, subject, group, week, teacher, room in rows:
                output += f"""
                <tr>
                    <td>{day}</td>
                    <td>{time_slot}</td>
                    <td>{subject}</td>
                    <td>{group}</td>
                    <td>{week}</td>
                    <td>{teacher}</td>
                    <td>{room}</td>
                </tr>
                """
        else:
            output += "<tr><td colspan='5'>No schedule data found.</td></tr>"

        output += "</table></body></html>"

        return output

    except Exception as e:
        return f"<p>Error fetching schedule: {e}</p>"


@app.teardown_appcontext
def shutdown_scheduler(exception=None):
    """Stop the schedulers when the app shuts down."""
    stop_scheduler()
    stop_lunch_scheduler()


@app.route('/api/current-period')
def current_period():
    data = find_current_period(get_db_connection)
    return json.dumps(data, ensure_ascii=False, indent=2)


@app.route('/api/today-lunch')
def today_lunch():
    """Return JSON for today's lunch matching frontend keys: soup, first, second, doplněk."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT meal_type, name FROM lunch WHERE date = CURRENT_DATE;")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        result = {"soup": None, "first": None, "second": None, "doplněk": None}

        for meal_type, name in rows:
            mt = (meal_type or '').strip().lower()
            if 'pol' in mt or 'soup' in mt:
                result['soup'] = name
            elif 'dopln' in mt or 'dop' in mt:
                result['doplněk'] = name
            elif mt.startswith('1') or mt in ('1', 'first'):
                result['first'] = name
            elif mt.startswith('2') or mt in ('2', 'second'):
                result['second'] = name
            else:
                if '1' in mt:
                    result['first'] = name
                elif '2' in mt:
                    result['second'] = name
                else:
                    result.setdefault(mt, name)

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False, indent=2)

@app.route('/api/lunch-schedule')
def lunch_schedule_api():
    """Return JSON with lunch schedule for 6 days."""
    try:
        schedule = get_lunch_schedule(get_db_connection, days=6)
        return json.dumps(schedule, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False, indent=2)

@app.route('/rozvrh-hodin')
def rozvrh_hodin():
    return render_template('rozvrh-hodin.html')

@app.route('/rozvrh-obedu')
def rozvrh_obedu():
    return render_template('rozvrh-obedu.html')


if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5000, debug=True)
