# SCBC — Simple Start (Monkey-proof) 🐒

A short, clear guide to fetch and upload a class schedule to the database. Follow these exact steps and you'll be done in under 5 minutes.

---

## Requirements ✅
- Python 3.8+ installed
- Internet access to fetch live schedules
- PostgreSQL reachable from this machine (host/port/user/pass should be set)
- Run commands from the project **root** (where `scbc/` lives)

---

## Quick 1‑2‑3: Upload a schedule (safe)

1) Open PowerShell and change to project folder:

```powershell
cd "C:\Users\<you>\Desktop\bakalari_strava_app 21.10"
```

2) Set DB credentials in the current PowerShell session (temporary, safe for testing):

```powershell
# Replace with your actual values (do not share the password)
$env:SCBC_DB_HOST = "localhost"
$env:SCBC_DB_NAME = "school_dashboard"
$env:SCBC_DB_USER = "postgres"
$env:SCBC_DB_PASSWORD = "<your-real-db-password>"
$env:SCBC_DB_PORT = "1325"
```

Tip: Use `setx` instead of `$env:` if you want the value to persist for future shells (requires a new terminal window):
```powershell
setx SCBC_DB_PASSWORD "<your-real-db-password>"
```

3) Run a dry-run first (this parses the schedule but does NOT write anything):

```powershell
python -m scbc.cli --code <4-letter-code> --class "<class-name>" --yes --dry-run
# example:
python -m scbc.cli --code truy --class "3.P" --yes --dry-run
```

If the dry-run looks correct (it prints number of entries and a summary), do the real upload:

```powershell
python -m scbc.cli --code <4-letter-code> --class "<class-name>" --yes
# example:
python -m scbc.cli --code truy --class "3.P" --yes
```

- The tool will **atomically replace** all rows for that `class_name` (delete old, insert new). It will NOT touch other classes.

4) Quick verification (count rows for a class):

```powershell
python -c "from scbc.db import ScheduleDB; db=ScheduleDB(); rows=db.get_schedule('3.P'); print('Inserted rows:', len(rows)); db.disconnect()"
```

---

## Listing all classes and counts (optional)

PowerShell multi-line snippet to see counts per class:

```powershell
python - <<'PY'
from scbc.db import ScheduleDB
 db=ScheduleDB()
 conn = db.connect()
 cur = conn.cursor()
 cur.execute("SELECT class_name, COUNT(*) FROM schedules GROUP BY class_name ORDER BY class_name;")
 print(cur.fetchall())
 cur.close()
 db.disconnect()
PY
```

(If you prefer, run the same snippet in a single-line Python -c invocation.)

---

## Troubleshooting ⚠️

- "No module named scbc": make sure you run Python from the project root (where `scbc/` folder sits). Use `cd` into the project folder first.
- "Password missing" or connection failures: ensure `SCBC_DB_PASSWORD` is set in **the same terminal session** before running the uploader. Use the connection test:

```powershell
python -c "from scbc.db import ScheduleDB; db=ScheduleDB(); import sys
try: db.connect(); print('OK: connected'); db.disconnect()
except Exception as e: print('ERROR:', e); sys.exit(1)"
```

- If the fetched page shows a different `class_name` than your target (e.g., you fetched `truy` but the page is `3.P`), that’s expected. You can save the fetched schedule under any `--class` you choose (e.g., save `3.P` schedule under `3.P`).

- The uploader intelligently **replaces only rows for the supplied `class_name`**. Uploading class `A` will not delete class `B`'s rows.

---

## Safety & tips 💡
- Always do a `--dry-run` first. It takes seconds and prevents mistakes.
- Back up your DB if you're working with production data before running large operations.
- Don't commit credentials to git. Use environment variables or a secure store.
- If you want automated DB tests, set `SCBC_RUN_DB_TEST=1` and run your test runner (requires reachable DB).

---

If you'd like, I can add a one-line `scbc` command to show `class_name` counts and a `--force` safety flag for destructive actions. Let me know which you'd prefer and I’ll add it.
