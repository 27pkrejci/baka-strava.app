"""
SCBC: School Class Bakaláři Converter
Refactored modules from stscbc.py for testable, modular code.

Main functions:
  - fetch_schedule_from_file(): Read HTML from local test file
  - fetch_schedule_from_network(): Fetch HTML from live URL  
  - sep_schedule(): Convert raw schedule to structured entries
"""

from .fetch import fetch_schedule_from_file, fetch_schedule_from_network
from .sep import sep_schedule

__all__ = ["fetch_schedule_from_file", "fetch_schedule_from_network", "sep_schedule"]
