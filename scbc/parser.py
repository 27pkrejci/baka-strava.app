"""
scbc/parser.py - Schedule parser that handles rowspans and multiple subject variants.

Core insight: 
- Each timeslot per day should emit exactly ONE entry (the first non-empty cell in that column)
- Cells with rowspan>1 should only emit from their first/top row, not repeated from subsequent rows
- Columns 2-3 contain different subject variants; we pick the first available one per timeslot
"""

import re


def normalize_day_name(text):
    """Extract and normalize day name from text."""
    if not text or not isinstance(text, str):
        return ""

    clean = "".join(text.split())
    
    day_map = {
        "po": "Po", "pondělí": "Po",
        "út": "Ut", "ú": "Ut", "úterý": "Ut",
        "st": "St", "středa": "St",
        "čt": "Ct", "čtvrtek": "Ct",
        "pá": "Pa", "pátek": "Pa",
        "so": "So", "sobota": "So",
        "ne": "Ne", "neděle": "Ne",
    }
    
    lower = clean.lower()
    return day_map.get(lower, "")


def is_empty_placeholder(text):
    """Check if cell is empty or placeholder."""
    if not text or not isinstance(text, str):
        return True
    t = " ".join(text.split()).strip()
    return t in ["", "&nbsp;", "nbsp", "o", "-- o --", "-- TH --"]


def parse_subject(cell):

    if not cell or not cell.get("elem"):
        return None, None, None, None
    
    elem = cell["elem"]
    full_text = elem.get_text(separator=" ", strip=True)
    
    if is_empty_placeholder(full_text):
        return None, None, None, None
    
    spans = elem.find_all("span")
    if not spans:
        return None, None, None, None
    
    subject = None
    group = None
    teacher = None
    room = None
    
    has_textsmaller = any("textsmaller_1" in span.get("class", []) for span in spans)
    
    if has_textsmaller:
        for i, span in enumerate(spans):
            text = span.get_text(strip=True)
            if not text:
                continue
            
            if i == 0:
                subject = text
            elif i == 1 and text.startswith("(") and text.endswith(")"):
                group = text[1:-1]
            elif i == 2:
                teacher = text
            elif i == 3 and text.startswith("(") and text.endswith(")"):
                room = text[1:-1]
    else:
        for i, span in enumerate(spans):
            text = span.get_text(strip=True)
            if not text:
                continue
            
            if i == 0:
                subject = text
            elif i == 1:
                if text.startswith("(") and text.endswith(")"):
                    inner = text[1:-1]
                    if inner.isdigit():
                        room = inner
                    else:
                        group = inner
                else:
                    teacher = text
            elif i == 2:
                if text.startswith("(") and text.endswith(")"):
                    room = text[1:-1]
                elif not teacher:
                    teacher = text
            elif i == 3 and text.startswith("(") and text.endswith(")"):
                room = text[1:-1]
    
    return subject, group, teacher, room


def build_full_grid(rows, num_timeslots):
    total_cols = len(rows[0]) if rows else 0
    
    col_blocked_until = [0] * total_cols
    
    grid = []
    
    for row_idx, row in enumerate(rows):
        grid_row = [None] * total_cols
        html_col_idx = 0
        
        for grid_col_idx in range(total_cols):
            if col_blocked_until[grid_col_idx] > row_idx:
                grid_row[grid_col_idx] = None
                continue
            
            if html_col_idx < len(row):
                cell = row[html_col_idx]
                grid_row[grid_col_idx] = cell
                rowspan = int(cell.get("rowspan", 1)) if cell else 1
                if rowspan > 1:
                    blocked_until_row = row_idx + rowspan
                    col_blocked_until[grid_col_idx] = max(col_blocked_until[grid_col_idx], blocked_until_row)
                
                html_col_idx += 1
            else:
                grid_row[grid_col_idx] = None
        
        grid.append(grid_row)
    
    return grid


def parse_schedule(raw_schedule, debug=False):
    entries = []
    entry_id = 1
    
    class_name = raw_schedule.get("class_name", "Unknown")
    time_slots = raw_schedule.get("time_slots", [])
    rows = raw_schedule.get("rows", [])
    
    if not time_slots or not rows:
        return entries
    
    if debug:
        print(f"DEBUG: Starting parse_schedule with {len(rows)} rows")
    
    grid = build_full_grid(rows, len(time_slots))
    
    if debug:
        print("DEBUG: Reconstructed grid (text,rowspan) per row:")
        for ri, gr in enumerate(grid):
            cells = []
            for c in gr:
                if c:
                    t = c.get("text", "").replace('\n', ' ').strip()
                    rs = c.get("rowspan", 1)
                    cells.append(f"'{t}'({rs})")
                else:
                    cells.append("None")
            print(f"  row {ri}: {', '.join(cells)}")
    
    day_info = []
    row_idx = 0
    while row_idx < len(grid):
        grid_row = grid[row_idx]
        if not grid_row:
            row_idx += 1
            continue
        
        day_marker_cell = None
        day_marker_col = None
        for col_idx in range(min(2, len(grid_row))):
            cell = grid_row[col_idx]
            if cell:
                day_candidate = normalize_day_name(cell.get("text", ""))
                if day_candidate:
                    day_marker_cell = cell
                    day_marker_col = col_idx
                    break
        
        if day_marker_cell:
            current_day = normalize_day_name(day_marker_cell.get("text", ""))
            day_rowspan = int(day_marker_cell.get("rowspan", 1))
            day_info.append((current_day, day_marker_col, row_idx, row_idx + day_rowspan))
            if debug:
                print(f"DEBUG: Found day '{current_day}' at row {row_idx}, spans to {row_idx + day_rowspan}")
            row_idx += day_rowspan
        else:
            row_idx += 1

    for day_name, day_marker_col, day_start_row, day_end_row in day_info:
        for timeslot_idx in range(len(time_slots)):
            time_slot = time_slots[timeslot_idx]
            col_idx = day_marker_col + 1 + timeslot_idx

            if col_idx >= len(grid[day_start_row]):
                continue
            
            if debug and day_name == "Po" and timeslot_idx <= 1:
                print(f"DEBUG: Processing {day_name} timeslot {timeslot_idx} at col {col_idx}")
            
            if debug and day_name == "Ut":
                print(f"DEBUG: Processing {day_name} timeslot {timeslot_idx} at col {col_idx}")

            for data_row_idx in range(day_start_row, day_end_row):
                if data_row_idx >= len(grid):
                    break
                
                data_grid_row = grid[data_row_idx]
                if col_idx >= len(data_grid_row):
                    continue
                
                cell = data_grid_row[col_idx]

                if not cell:
                    if debug and day_name == "Po" and timeslot_idx <= 1:
                        print(f"  Row {data_row_idx}: EMPTY")
                    if debug and day_name == "Ut":
                        print(f"  Row {data_row_idx}: EMPTY")
                    continue

                if is_empty_placeholder(cell.get("text", "")):
                    if debug and day_name == "Po" and timeslot_idx <= 1:
                        print(f"  Row {data_row_idx}: PLACEHOLDER")
                    if debug and day_name == "Ut":
                        print(f"  Row {data_row_idx}: PLACEHOLDER")
                    continue

                is_top_of_rowspan = True
                for check_row_idx in range(day_start_row, data_row_idx):
                    check_cell = grid[check_row_idx][col_idx] if col_idx < len(grid[check_row_idx]) else None
                    if check_cell:
                        check_rowspan = int(check_cell.get("rowspan", 1))
                        if check_row_idx + check_rowspan > data_row_idx:
                            is_top_of_rowspan = False
                            break
                
                if not is_top_of_rowspan:
                    if debug and day_name == "Po" and timeslot_idx <= 1:
                        print(f"  Row {data_row_idx}: COVERED by earlier rowspan, skip")
                    continue
                
                subject, group, teacher, room = parse_subject(cell)
                cell_text = cell.get("text", "").strip() if isinstance(cell.get("text", ""), str) else ""

                if not subject and cell_text and not is_empty_placeholder(cell_text):
                    subject = cell_text
                    group = None
                    teacher = None
                    room = None

                if subject:
                    if debug and day_name == "Po" and timeslot_idx <= 1:
                        print(f"  Row {data_row_idx}: {subject} ({group}) -> EMIT")
                    entry = {
                        "rid": str(entry_id),
                        "day": day_name,
                        "time_slot": time_slot,
                        "subject": subject,
                        "group": group,
                        "teacher": teacher,
                        "room": room,
                    }
                    entries.append(entry)
                    entry_id += 1
                    if debug:
                        cell_text = cell.get("text", "")
                        rowspan = int(cell.get("rowspan", 1))
                        print(f"TRACE: emit day={day_name} ts={timeslot_idx} col={col_idx} row={data_row_idx} text='{cell_text}' rowspan={rowspan}")
    
    print(f"Processed {len(entries)} entries in parse_schedule.")
    return entries
