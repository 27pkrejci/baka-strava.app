"""
Utilities for cleaning and parsing schedule data.
"""
import re


def clean_timeslot(ts_raw):
    """Remove leading timeslot number (1-10) from time slot string.
    
    The HTML has format like:
      "<span>1</span><br>8:00- 8:45" which becomes "1\n8:00- 8:45" after extraction
    This function should only remove the leading digit and whitespace, not hour digits.
    
    Examples:
      "1 8:00- 8:45" -> "8:00- 8:45"
      "10 16:25-17:10" -> "16:25-17:10"
      "8:00- 8:45" -> "8:00- 8:45" (already clean)
    """
    # Match 1-2 digits at the very start, followed by whitespace/newlines
    # But only if it looks like a timeslot number (1-10)
    match = re.match(r"^(\d{1,2})\s*", ts_raw)
    if match:
        potential_number = int(match.group(1))
        # Only remove if it looks like a slot number (1-10)
        if 1 <= potential_number <= 10:
            return ts_raw[match.end():].strip()
    
    # If no clear match, just strip leading/trailing whitespace
    return ts_raw.strip()


def parse_subject(cell):
    """Parse a schedule cell into subject, teacher, room and group.

    The `cell` argument is expected to be a dict created by `fetch.py` with keys:
      - 'text': full text of the cell
      - 'elem': BeautifulSoup Tag for the td (optional)
      - 'rowspan': integer

    Structure expected:
      - Subject: in a bold span (textlargebold_1)
      - Group: comma-separated text (optional), e.g. ", GroupName"
      - Teacher: text after subject/group, often in textnormal_1 span
      - Room: in parentheses at the end, e.g. "(15)"

    Returns: (subject, teacher, room, group)
    """
    full_text = (cell.get("text") or "").strip()
    elem = cell.get("elem")

    subject = None
    teacher = None
    room = None
    group = None

    # Extract room: last numeric value in parentheses
    room_match = re.search(r"\((\d+)\)\s*$", full_text)
    room = room_match.group(1) if room_match else None

    # Use element spans if available
    if elem:
        # Subject: first span with textlargebold_1 class (bold text, usually subject code)
        subj_span = elem.find("span", class_="textlargebold_1")
        if subj_span:
            subject = subj_span.get_text(strip=True)
            if not subject or re.match(r"^[^a-zA-Z]", subject):
                # Not a valid subject, skip
                subject = None

        # Collect all textnormal_1 spans (usually contain group and teacher)
        normal_spans = elem.find_all("span", class_="textnormal_1")
        if normal_spans:
            # Join all textnormal_1 spans with their text
            normal_texts = []
            for span in normal_spans:
                text = span.get_text(strip=True)
                if text:
                    normal_texts.append(text)
            
            # Reconstruct the comma-separated and newline-separated content
            full_normal = " ".join(normal_texts)
            
            # Extract group: text between commas
            group_match = re.search(r",\s*([^,()]+?)(?:\s|$|,)", full_normal)
            if group_match:
                group = group_match.group(1).strip()
            
            # Extract teacher: text that follows group and isn't in parentheses
            # Remove group from the text
            temp = full_normal
            if group:
                temp = temp.replace(f", {group}", "").replace(f",{group}", "")
            
            # Remove room info
            if room:
                temp = re.sub(r"\(\d+\)", "", temp)
            
            # Clean up and extract teacher
            temp = re.sub(r"[(),]", " ", temp).strip()
            parts = [p.strip() for p in temp.split() if p.strip()]
            
            if parts:
                # Teacher is usually the remaining token
                teacher = parts[0] if len(parts) == 1 else " ".join(parts)

    # Fallback parsing if element parsing didn't work
    if not subject:
        # Subject is the first token before comma or special characters
        match = re.match(r"^([a-zA-Z]+)", full_text)
        if match:
            subject = match.group(1)

    # If we still don't have teacher or group, try to extract from full_text
    if not group:
        # Group is comma-separated value
        group_match = re.search(r",\s*([^,()]+?)(?:\s|,|$)", full_text)
        if group_match:
            potential_group = group_match.group(1).strip()
            # Make sure it's not a person name (usually 2-3 chars for subject codes)
            if potential_group and not potential_group.startswith("("):
                group = potential_group

    if not teacher:
        # Extract remaining text for teacher
        temp = full_text
        if subject:
            temp = temp.replace(subject, "", 1)
        if group:
            temp = temp.replace(f", {group}", "").replace(f",{group}", "")
        if room:
            temp = re.sub(r"\(\d+\)", "", temp)
        
        # Clean and extract
        temp = re.sub(r"[(),]", " ", temp).strip()
        parts = [p.strip() for p in temp.split() if p.strip() and len(p.strip()) > 0]
        if parts:
            # Take the first remaining part as teacher
            teacher = parts[0]

    # Normalize empty values to None
    subject = subject if subject and len(subject) > 0 else None
    teacher = teacher if teacher and len(teacher) > 0 else None
    room = room if room else None
    group = group if group and len(group) > 0 else None

    return (subject, teacher, room, group)