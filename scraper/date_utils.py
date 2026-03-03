"""Parse and normalize episode dates to YYYY-MM-DD."""

from __future__ import annotations

import re
from datetime import datetime

MONTH_ABBREV = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def parse_date(date_str: str) -> str | None:
    """
    Parse date string to YYYY-MM-DD. Handles:
    - "Feb 19, 2026"
    - "February 19, 2026"
    - "Jan 1, 2026"
    Returns None if unparseable.
    """
    if not date_str or not date_str.strip():
        return None
    s = date_str.strip()
    # Try full month name first (e.g. February 19, 2026)
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%d %B %Y", "%d %b %Y"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Manual abbrev lookup for "Feb 19, 2026" style
    m = re.match(r"(\w+)\s+(\d{1,2}),?\s+(\d{4})", s, re.I)
    if m:
        month_str, day, year = m.groups()
        month = MONTH_ABBREV.get(month_str.lower()[:3])
        if month is not None:
            try:
                day_int = int(day)
                year_int = int(year)
                if 1 <= day_int <= 31 and 1900 <= year_int <= 2100:
                    return f"{year_int:04d}-{month:02d}-{day_int:02d}"
            except ValueError:
                pass
    return None
