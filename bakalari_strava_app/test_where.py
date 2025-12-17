# test_where.py - spusť v bakalari_strava_app
import psycopg2

# Test 1: Kam se připojuje db_3p.py?
print("🧪 Testuji db_3p.py připojení (localhost:1325):")
try:
    conn1 = psycopg2.connect(
        host="localhost",
        port=1325,
        dbname="school_dashboard",
        user="postgres",
        password="dat224551"
    )
    cur1 = conn1.cursor()
    cur1.execute("SELECT COUNT(*) FROM timetable_3p")
    count1 = cur1.fetchone()[0]
    print(f"✅ db_3p.py vidí {count1} řádků v timetable_3p")
    conn1.close()
except Exception as e:
    print(f"❌ db_3p.py chyba: {e}")

print("\n🧪 Testuji app.py připojení (localhost:1325):")
try:
    conn2 = psycopg2.connect(
        host="localhost", 
        port=1325,
        dbname="school_dashboard",
        user="postgres",
        password="dat224551"
    )
    cur2 = conn2.cursor()
    cur2.execute("SELECT COUNT(*) FROM timetable_3p")
    count2 = cur2.fetchone()[0]
    print(f"✅ app.py vidí {count2} řádků v timetable_3p")
    conn2.close()
except Exception as e:
    print(f"❌ app.py chyba: {e}")