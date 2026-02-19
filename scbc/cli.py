"""
scbc/cli.py - Simple CLI for uploading schedules into the DB.

Usage:
    python -m scbc.cli   # interactive
    python -m scbc.cli --code truy --class "7.G" --yes   # non-interactive

The module provides a programmatic `upload_schedule` function for automated use.
"""

import argparse
import sys
from typing import List, Dict

from .fetch import fetch_schedule_from_network
from .parser import parse_schedule
from .db import ScheduleDB


def upload_schedule(code: str, class_name: str, confirm: bool = True, dry_run: bool = False, debug: bool = False) -> int:
    """Fetch, parse and upload schedule for `code` and save as `class_name`.

    When ``debug`` is true the parser is run in verbose mode and the
    resulting entries are printed to the terminal (even in dry-run).

    Returns number of inserted rows on success. Raises on error.
    """
    if not code or not class_name:
        raise ValueError("code and class_name must be provided")

    raw = fetch_schedule_from_network(code)
    entries = parse_schedule(raw, debug=debug)

    if not entries:
        raise RuntimeError("No entries parsed; aborting upload")

    if debug:
            # print the parsed entries in a readable table-like form
            print("\nParsed entries:")
            for e in entries:
                line = f"  {e['day']} {e['time_slot']} - {e['subject']}"
                line += f" (group={e['group']}, teacher={e['teacher']}, room={e['room']})"
                if e.get('week'):
                    line += f" [week={e['week']}]"
                print(line)
            print()
    if dry_run:
        print(f"[DRY RUN] Would upload {len(entries)} entries for {class_name}")
        return len(entries)

    if confirm:
        user_confirm = input(f"Ready to save {len(entries)} entries to database as '{class_name}'? (yes/no): ").strip().lower()
        if user_confirm != "yes":
            raise KeyboardInterrupt("User cancelled")

    db = ScheduleDB()
    try:
        print(f"[UPDATING] Replacing schedule for '{class_name}' (delete old, insert new) ...")
        count = db.replace_schedule_entries(class_name, entries)
        print(f"[OK] Successfully saved {count} entries!")
        return count
    finally:
        db.disconnect()


def _parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Upload a Bakaláři schedule to the database")
    p.add_argument("--code", help="4-letter schedule code (e.g., 'truy')")
    p.add_argument("--class", dest="class_name", help="Class name to store in DB, e.g. '7.G'")
    p.add_argument("--yes", dest="yes", action="store_true", help="Skip confirmation (non-interactive) ")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", help="Do everything except write to DB")
    p.add_argument("--debug", dest="debug", action="store_true",
                   help="Enable parser debug output and show parsed entries")
    return p.parse_args(argv)


def main(argv: List[str] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    args = _parse_args(argv)

    if not args.code or not args.class_name:
        print("Interactive mode: you can also pass --code and --class.\n")
        code = input("Enter your schedule code (e.g., 'truy'): ").strip()
        class_name = input("Enter your class name (e.g., '7.G'): ").strip()
        args.code = args.code or code
        args.class_name = args.class_name or class_name

    try:
        inserted = upload_schedule(
            args.code,
            args.class_name,
            confirm=not args.yes,
            dry_run=args.dry_run,
            debug=args.debug,
        )
        print("Done.")
        return 0
    except KeyboardInterrupt:
        print("Cancelled by user.")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())