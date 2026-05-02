#!/usr/bin/env python3
"""
rebuild_index.py — Regenerate the _events array in index.html from ArizonaHorseCalendar.csv
Run after any CSV update to keep the live calendar in sync.
Usage: python3 rebuild_index.py
"""
import csv
import json
import re
import os
from datetime import datetime

CSV_PATH = os.path.join(os.path.dirname(__file__), 'ArizonaHorseCalendar.csv')
HTML_PATH = os.path.join(os.path.dirname(__file__), 'index.html')

with open(CSV_PATH, 'r', newline='', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    events = list(reader)

events_json = json.dumps(events, ensure_ascii=False, separators=(', ', ': '))

with open(HTML_PATH, 'r', encoding='utf-8') as f:
    html = f.read()

start_marker = 'const _events = ['
start_idx = html.find(start_marker)
if start_idx == -1:
    raise ValueError("Could not find 'const _events = [' in index.html")

end_match = re.search(r'\}\];\s*\n', html[start_idx:])
if not end_match:
    raise ValueError("Could not find end of _events array in index.html")

abs_end = start_idx + end_match.end()
new_block = f'const _events = {events_json};\n'
new_html = html[:start_idx] + new_block + html[abs_end:]

with open(HTML_PATH, 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] index.html rebuilt — {len(events)} events from CSV")
