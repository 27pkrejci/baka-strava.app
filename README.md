# School Schedule Automation System

A complete Python application for parsing, storing, and automatically updating school schedules from the Bakaláři scheduling system (used by Czech schools).

## Features

✅ **Automatic Class Discovery**: Finds all classes from https://www.dgkralupy.cz/studium/rozvrhy-hodin/  
✅ **Hourly Auto-Updates**: Automatically updates all class schedules every hour (configurable)  
✅ **Background Scheduling**: Runs without blocking the web server  
✅ **Robust HTML Parsing**: Handles complex HTML tables with rowspans and colspan attributes  
✅ **Character Encoding**: Fixes Windows-1250 Czech character issues  
✅ **PostgreSQL Storage**: Persists all schedules in a database  
✅ **Flask Web Interface**: View schedules and lunch menus via web dashboard  

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Start the Flask application
python app.py
```

The application will:
1. Initialize the PostgreSQL database
2. Start the background scheduler
3. Update all class schedules every hour automatically
4. Serve the web interface at http://localhost:5000

### Configuration

Edit `scbc/config.py` to set your PostgreSQL credentials:

```python
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "schedule_db"
DB_USER = "postgres"
DB_PASSWORD = "your_password"
```

Or use environment variables:
```bash
export SCBC_DB_HOST=localhost
export SCBC_DB_PORT=5432
export SCBC_DB_NAME=schedule_db
export SCBC_DB_USER=postgres
export SCBC_DB_PASSWORD=your_password
```

### Web Interface

Once running, access the dashboard at `http://localhost:5000`:
- **`/`** - Home dashboard
- **`/lunch`** - Lunch menu
- **`/schedule`** - Class schedule

## How It Works

### Architecture

```
Flask Web Server (app.py)
    ↓ starts on boot
Background Scheduler (APScheduler)
    ↓ every hour
Discover Classes (scbc/class_list.py)
    ↓ for each class
Fetch & Parse Schedule (scbc/fetch.py + scbc/parser.py)
    ↓
Update PostgreSQL Database
    ↓
Log Results
```

### Automatic Updates

The system automatically:
1. **Discovers Classes** - Fetches the class list from the school website
2. **Fetches Schedules** - Downloads schedule HTML for each class
3. **Parses Data** - Extracts subjects, teachers, rooms, time slots
4. **Stores Results** - Saves to PostgreSQL database
5. **Logs Activity** - Records success/failure for monitoring

### Customizing Update Interval

Edit `app.py` to change the update schedule:

```python
# In the initialize_database() function, change:
schedule_update_task(hours=1)  # Every 1 hour (default)
schedule_update_task(hours=2)  # Every 2 hours
schedule_update_task(hours=24) # Daily
schedule_update_task(hours=0.5) # Every 30 minutes
```

## API & Usage

### Using the SCBC Module

```python
from scbc.class_list import fetch_classes_from_school
from scbc.fetch import fetch_schedule_from_network
from scbc.parser import parse_schedule

# Get all classes
classes = fetch_classes_from_school()

# Fetch a specific schedule
raw = fetch_schedule_from_network("truk")  # 7.G
entries = parse_schedule(raw)

# entries is a list of dicts with:
# {
#   "rid": "1",
#   "day": "Po",          # Monday
#   "time_slot": "8:00-8:45",
#   "subject": "Dg",
#   "group": None,
#   "teacher": "Bag",
#   "room": "15"
# }
```

### Manual Database Update

Update a specific class without waiting for the scheduler:

```bash
python -m scbc.cli --code truk --class "7.G" --yes
```

## Project Structure

```
.
├── app.py                    # Flask web application
├── scbc/                     # Schedule parsing package
│   ├── __init__.py
│   ├── class_list.py         # Discover classes from website
│   ├── scheduler.py          # Background job scheduler
│   ├── cli.py                # Command-line interface
│   ├── config.py             # Configuration
│   ├── db.py                 # Database operations
│   ├── fetch.py              # Schedule fetching
│   ├── parser.py             # Schedule parsing
│   └── utils.py              # Utility functions
├── scbc_tests/               # Test suite
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```
