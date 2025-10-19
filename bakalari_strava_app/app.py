from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import psycopg2

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:dat224551@localhost:1325/school_dashboard'

db = SQLAlchemy(app)
migrate = Migrate(app,db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))

# Database connection function
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        port=1325,
        database="school_dashboard",
        user="postgres",
        password="dat224551"
    )
@app.route('/')
def home():
    output = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>School Dashboard</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 50px;
                background-color: #f5f5f5;
            }
            h1 {
                color: #2c3e50;
                margin-bottom: 50px;
            }
            .dashboard-box {
                display: inline-block;
                margin: 20px;
                padding: 30px;
                background-color: #3498db;
                border-radius: 10px;
                color: white;
                width: 200px;
                height: 100px;
                text-align: center;
                font-size: 18px;
                vertical-align: middle;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                transition: 0.3s;
            }
            .dashboard-box a {
                text-decoration: none;
                color: white;
                display: block;
                width: 100%;
                height: 100%;
                line-height: 100px;
            }
            .dashboard-box:hover {
                background-color: #2980b9;
                transform: translateY(-5px);
                box-shadow: 0 6px 12px rgba(0,0,0,0.3);
                cursor: pointer;
            }
            footer {
                margin-top: 50px;
                color: #555;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <h1>School Dashboard</h1>

        <div class="dashboard-box">
            <a href="/lunch">Lunch Menu</a>
        </div>

        <div class="dashboard-box">
            <a href="/schedule">Class Schedule</a>
        </div>

        <footer>&copy; 2025 Your School Dashboard</footer>
    </body>
    </html>
    """
    return output


@app.route('/lunch')
def lunch():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT day, menu FROM lunch ORDER BY day;")
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
                table { border-collapse: collapse; width: 60%; }
                th, td { border: 1px solid #999; padding: 8px; text-align: left; }
                th { background-color: #eee; }
            </style>
        </head>
        <body>
            <h2>Lunch Menu</h2>
            <table>
                <tr><th>Day</th><th>Menu</th></tr>
        """

        if rows:
            for day, menu in rows:
                output += f"<tr><td>{day}</td><td>{menu}</td></tr>"
        else:
            output += "<tr><td colspan='2'>No lunch data found.</td></tr>"

        output += "</table></body></html>"

        return output

    except Exception as e:
        return f"<p>Error fetching lunch menu: {e}</p>"

@app.route('/schedule')
def schedule():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT day, period, subject, teacher, room FROM classes ORDER BY day, period;")
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
                    <th>Period</th>
                    <th>Subject</th>
                    <th>Teacher</th>
                    <th>Room</th>
                </tr>
        """

        if rows:
            for day, period, subject, teacher, room in rows:
                output += f"""
                <tr>
                    <td>{day}</td>
                    <td>{period}</td>
                    <td>{subject}</td>
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

if __name__ == '__main__':
    app.run(debug=True)
