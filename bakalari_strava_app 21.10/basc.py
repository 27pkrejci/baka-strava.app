from bakapi import BakapiUser
import psycopg2

# Step 1: Authenticate
url = 'https://bakalari.dgkralupy.cz'
username = 'Krejc25241'
password = '6kgjiW0N'

user = BakapiUser(url=url, username=username, password=password)

# Step 2: Fetch schedule data
schedule = user.query_api('/schedule_endpoint')  # Use the actual API endpoint

# Step 3: Connect to PostgreSQL
conn = psycopg2.connect("dbname=school_dashboard user=postgres password=dat224551 host=localhost port=1325")
cur = conn.cursor()

# Step 4 & 5: Create table and insert/update data (example)
cur.execute('''
CREATE TABLE IF NOT EXISTS schedules (
    id SERIAL PRIMARY KEY,
    class TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    subject TEXT,
    room TEXT
);
''')

for entry in schedule['data']:
    cur.execute('''
    INSERT INTO schedules (class, start_time, end_time, subject, room)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT DO NOTHING;
    ''', (entry['class'], entry['start'], entry['end'], entry['subject'], entry['room']))

conn.commit()
cur.close()
conn.close()
