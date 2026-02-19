from .utils import parse_subject

def sep_schedule(raw_schedule):

    time_slots_raw = raw_schedule["time_slots"]
    time_slots = time_slots_raw

    rows_list = raw_schedule["rows"]
    day_names = ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"]

    structured_schedule = []
    rid = 1
    current_day = None

    VIRTUAL_BOXES = 10
    MAX_ROWSPAN = 10

    day_grid = [0] * VIRTUAL_BOXES

    global_row_idx = 0

    for row in rows_list:
        used_boxes_this_row = [False] * VIRTUAL_BOXES
        col_idx = 0
        is_new_day = False

        if len(row) > 1:
            second_td_text = row[1]["text"].strip()
            second_td_normalized = second_td_text.replace("\n", "").replace(" ", "").strip()
            if second_td_normalized in day_names or second_td_normalized in ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"]:
                current_day = second_td_normalized
                day_grid = [0] * VIRTUAL_BOXES
                is_new_day = True
                col_idx = 2
            else:
                col_idx = 1 
        else:
            col_idx = 1

        while col_idx < len(row):

            if col_idx == 0 or col_idx == len(row) - 1:
                col_idx += 1
                continue

            cell = row[col_idx]
            cell_text = cell.get("text", "").strip()
            rowspan = cell.get("rowspan", 1)

            if not cell_text or cell_text in ["-- o --", "-- TH --", "&nbsp;"]:
                col_idx += 1
                continue

            subject, teacher, room, group, week = parse_subject(cell)

            if not subject:
                col_idx += 1
                continue

            box_idx = 0
            for box_idx, box_value in enumerate(day_grid):
                if not used_boxes_this_row[box_idx] and box_value == 0:
                    break
            else:
                for box_idx in range(len(day_grid)):
                    if not used_boxes_this_row[box_idx]:
                        break

            ts_idx = box_idx if box_idx < len(time_slots) else len(time_slots) - 1
            time_slot = time_slots[ts_idx]

            entry = {
                    "rid": rid,
                    "day": current_day,
                    "time_slot": time_slot,
                    "subject": subject,
                    "group": group,
                    "teacher": teacher,
                    "room": room,
            }
            if week:
                entry["week"] = week
            structured_schedule.append(entry)
            rid += 1

            day_grid[box_idx] = rowspan
            used_boxes_this_row[box_idx] = True

            col_idx += 1

        for i in range(len(day_grid)):
            if day_grid[i] > 0:
                day_grid[i] -= 1

        global_row_idx += 1

    print(f"Processed {len(structured_schedule)} entries in sep_schedule.")
    return structured_schedule
