import os
from typing import Optional

DB_HOST = os.getenv("SCBC_DB_HOST", "localhost")
DB_NAME = os.getenv("SCBC_DB_NAME", "school_dashboard")
DB_USER = os.getenv("SCBC_DB_USER", "postgres")
DB_PASSWORD = os.getenv("SCBC_DB_PASSWORD", "dat224551")
DB_PORT = int(os.getenv("SCBC_DB_PORT", "1325"))

def db_dsn_no_password() -> str:
    return f"host={DB_HOST} dbname={DB_NAME} user={DB_USER} port={DB_PORT}"

BASE_URL = os.getenv("SCBC_BASE_URL", "https://www.dgkralupy.cz/BakaFiles/rozvrh/")

SCHEDULE_TABLE_INDEX = int(os.getenv("SCBC_SCHEDULE_TABLE_INDEX", "1")) 
HEADER_ROWS = int(os.getenv("SCBC_HEADER_ROWS", "4"))