#!/usr/bin/env python3
"""
export_bridle_bit.py — Export ArizonaHorseCalendar.csv as InDesign-ready RTF
Sorted by Category, then by StartDate.
Output: BridleBit_Events.rtf

Usage: python3 export_bridle_bit.py
       python3 export_bridle_bit.py --az-only       (Arizona events only)
       python3 export_bridle_bit.py --upcoming-only  (Future/current events only)
"""

import csv
import os
import sys
import re
from datetime import datetime, date

# ── CONFIG ────────────────────────────────────────────────────────────────────
CSV_PATH  = os.path.join(os.path.dirname(__file__), 'ArizonaHorseCalendar.csv')
RTF_PATH  = os.path.join(os.path.dirname(__file__), 'BridleBit_Events.rtf')

AZ_ONLY       = '--az-only'       in sys.argv
UPCOMING_ONLY = '--upcoming-only' in sys.argv
TODAY         = date.today()

# Category display order (most equestrian-relevant first)
CATEGORY_ORDER = [
    'Team Roping', 'Barrel Racing', 'Rodeo', 'Bull Riding',
    'Gymkhana', 'Cutting', 'Reining', 'Reined Cow Horse', 'Cow Horse',
    'Ranch Versatility', 'Ranch Sorting', 'Team Penning', 'Cattle Sorting',
    'Working Equitation', 'Western', 'Stock Horse',
    'Hunter/Jumper', 'Dressage', 'Arabian Horse Show', 'Paint Horse Show',
    'Quarter Horse Show', 'Breed Show',
    'Obstacle Course', 'Mounted Shooting', 'Polo',
    'Trail Ride', 'Clinic', 'Horse Show',
    'Youth Horse Camp', 'Youth Program', 'Youth Event',
    'Community Event', 'Fundraiser', 'Concert',
    'Rodeo Queen', 'Equine Art',
]

# ── DATE PARSING ──────────────────────────────────────────────────────────────
MONTH_NAMES = {
    1:'January',2:'February',3:'March',4:'April',5:'May',6:'June',
    7:'July',8:'August',9:'September',10:'October',11:'November',12:'December'
}

def parse_date(s):
    """Return (date_object, sort_key). Recurring/unknown events sort last."""
    if not s or not s[0].isdigit():
        return None, (9999, 12, 31, s)
    for fmt in ('%m/%d/%y', '%m/%d/%Y', '%Y-%m-%d'):
        try:
            d = datetime.strptime(s.strip(), fmt).date()
            return d, (d.year, d.month, d.day, '')
        except ValueError:
            continue
    return None, (9999, 12, 31, s)

def format_date_range(start_str, end_str):
    """Return human-readable date range: 'May 22–23, 2026' or 'May 22, 2026'"""
    sd, _ = parse_date(start_str)
    ed, _ = parse_date(end_str)
    if not sd:
        return start_str or 'Date TBD'
    if not ed or sd == ed:
        return f"{MONTH_NAMES[sd.month]} {sd.day}, {sd.year}"
    if sd.month == ed.month and sd.year == ed.year:
        return f"{MONTH_NAMES[sd.month]} {sd.day}\u2013{ed.day}, {sd.year}"
    if sd.year == ed.year:
        return f"{MONTH_NAMES[sd.month]} {sd.day}\u2013{MONTH_NAMES[ed.month]} {ed.day}, {sd.year}"
    return f"{MONTH_NAMES[sd.month]} {sd.day}, {sd.year}\u2013{MONTH_NAMES[ed.month]} {ed.day}, {ed.year}"

# ── RTF ESCAPING ──────────────────────────────────────────────────────────────
def rtf_escape(text):
    """Escape a string for RTF output."""
    if not text:
        return ''
    out = []
    for ch in str(text):
        cp = ord(ch)
        if ch == '\\': out.append('\\\\')
        elif ch == '{':  out.append('\\{')
        elif ch == '}':  out.append('\\}')
        elif ch == '\n': out.append('\\line ')
        elif cp < 128:   out.append(ch)
        elif cp <= 255:  out.append(f"\\'{cp:02x}")
        else:            out.append(f"\\u{cp}?")
    return ''.join(out)

def e(text):
    return rtf_escape(text)

# ── RTF PARAGRAPH HELPERS ─────────────────────────────────────────────────────
def para(style_num, content, extra=''):
    """Wrap content in an RTF paragraph with named style."""
    return f"{{\\pard\\s{style_num}{extra} {content}\\par}}\n"

def category_head(text):
    # Style 1: Category heading — bold, 11pt, space before
    return para(1, f"\\b {e(text)}\\b0")

def event_name(text):
    # Style 2: Event name — bold, 9pt
    return para(2, f"\\b {e(text)}\\b0")

def event_meta(text):
    # Style 3: Date / Venue / City — 8pt
    return para(3, e(text))

def event_body(text):
    # Style 4: Description — 8pt, justified
    return para(4, e(text))

def event_contact(text):
    # Contact line — 10pt bold, centered, inline (no stylesheet)
    return f"{{\\pard\\qc\\f0\\fs20\\b\\sl240\\slmult0 {e(text)}\\b0\\par}}\n"

def divider():
    # Thin rule between events (blank paragraph with bottom border)
    return "{\\pard\\s6\\sb0\\sa60 \\par}\n"

# ── LOAD & FILTER ─────────────────────────────────────────────────────────────
with open(CSV_PATH, 'r', newline='', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

if AZ_ONLY:
    rows = [r for r in rows if r.get('State','').strip().upper() == 'AZ']

if UPCOMING_ONLY:
    filtered = []
    for r in rows:
        d, _ = parse_date(r.get('StartDate',''))
        if d is None or d >= TODAY:
            filtered.append(r)
    rows = filtered

# ── SORT: Category order, then by StartDate ───────────────────────────────────
def sort_key(r):
    cat = r.get('Category','').strip()
    try:
        cat_idx = CATEGORY_ORDER.index(cat)
    except ValueError:
        cat_idx = len(CATEGORY_ORDER)
    _, date_sort = parse_date(r.get('StartDate',''))
    return (cat_idx, cat, date_sort)

rows.sort(key=sort_key)

# ── GROUP BY CATEGORY ─────────────────────────────────────────────────────────
from itertools import groupby
grouped = []
for cat, group in groupby(rows, key=lambda r: r.get('Category','').strip() or 'Uncategorized'):
    grouped.append((cat, list(group)))

# ── BUILD RTF ─────────────────────────────────────────────────────────────────
pub_date = TODAY.strftime('%B %d, %Y')
total_events = len(rows)

rtf_parts = []

# RTF header
rtf_parts.append(
r"""{\rtf1\ansi\ansicpg1252\deff0
{\fonttbl
{\f0\fswiss\fcharset0 Helvetica;}
{\f1\fswiss\fcharset0 Arial;}
{\f2\froman\fcharset0 Times New Roman;}
}
{\colortbl;\red0\green0\blue0;\red90\green60\blue20;\red80\green80\blue80;}
{\stylesheet
{\s1\f1\fs22\b\sb240\sa60\cf2 Category Head;}
{\s2\f1\fs18\b\sb120\sa0 Event Name;}
{\s3\f1\fs16\sb0\sa0\cf3 Event Meta;}
{\s4\f0\fs16\sb40\sa0\qj Event Body;}
{\s5\f0\fs14\sb0\sa60\i\cf3 Event Contact;}
{\s6\f0\fs8\sb0\sa60 Event Divider;}
}
""")

# Document title block
rtf_parts.append(
    f"{{\\pard\\s1\\qc\\fs28\\b BRIDLE \\cf2&\\cf0 BIT MAGAZINE\\par}}\n"
    f"{{\\pard\\s3\\qc ARIZONA EQUESTRIAN EVENTS CALENDAR\\par}}\n"
    f"{{\\pard\\s3\\qc Generated {e(pub_date)} \\u8212? {total_events} Events\\par}}\n"
    f"{{\\pard\\s6 \\par}}\n"
)

# Events by category
for cat, events in grouped:
    rtf_parts.append(category_head(cat.upper()))

    for i, r in enumerate(events):
        # Event Name
        rtf_parts.append(event_name(r.get('EventName', '').strip()))

        # Date + Time
        date_str = format_date_range(r.get('StartDate',''), r.get('EndDate',''))
        time_str = r.get('Time','').strip()
        if time_str:
            date_str += f"  |  {time_str}"
        rtf_parts.append(event_meta(date_str))

        # Venue + City/State
        venue = r.get('Venue','').strip()
        city  = r.get('City','').strip()
        state = r.get('State','').strip()
        addr  = r.get('Address','').strip()
        loc_parts = []
        if venue:  loc_parts.append(venue)
        if addr:   loc_parts.append(addr)
        if city:   loc_parts.append(city)
        if state:  loc_parts.append(state)
        if loc_parts:
            rtf_parts.append(event_meta('  '.join(loc_parts)))

        # EventType / Division / Prize
        type_str = r.get('EventType','').strip()
        prize    = r.get('PrizeMoney','').strip()
        meta2_parts = []
        if type_str: meta2_parts.append(type_str)
        if prize:    meta2_parts.append(prize)
        if meta2_parts:
            rtf_parts.append(event_meta('  |  '.join(meta2_parts)))

        # Description
        desc = r.get('Description','').strip()
        if desc:
            rtf_parts.append(event_body(desc))

        # Contact line
        contact_parts = []
        phone   = r.get('Phone','').strip()
        email   = r.get('Email','').strip()
        website = r.get('Website','').strip()
        if phone:   contact_parts.append(phone)
        if email:   contact_parts.append(email)
        if website: contact_parts.append(website)
        if contact_parts:
            rtf_parts.append(event_contact('  |  '.join(contact_parts)))

        # Divider between events (not after last in category)
        if i < len(events) - 1:
            rtf_parts.append(divider())

    # Extra space after each category
    rtf_parts.append("{\\pard\\s6\\sb0\\sa120 \\par}\n")

rtf_parts.append("}")  # close RTF

# ── WRITE OUTPUT ──────────────────────────────────────────────────────────────
rtf_content = ''.join(rtf_parts)
with open(RTF_PATH, 'w', encoding='ascii', errors='replace') as f:
    f.write(rtf_content)

print(f"[{pub_date}] BridleBit_Events.rtf written — {total_events} events across {len(grouped)} categories")
print(f"Output: {RTF_PATH}")
if AZ_ONLY:       print("Filter: Arizona events only")
if UPCOMING_ONLY: print("Filter: Upcoming/current events only")
