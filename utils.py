# utils.py

import re

async def get_seconds(time_str: str) -> int:
    """
    Converts:
    '1 day', '7 days', '1 month', '3 months', '1 year', '10 min', '2 hours'
    into seconds
    """
    time_str = time_str.strip().lower()

    match = re.match(r"(\d+)\s*(day|days|hour|hours|min|mins|minute|minutes|month|months|year|years)", time_str)
    if not match:
        return 0

    num = int(match.group(1))
    unit = match.group(2)

    if "min" in unit:
        return num * 60
    if "hour" in unit:
        return num * 3600
    if "day" in unit:
        return num * 86400
    if "month" in unit:
        return num * 30 * 86400
    if "year" in unit:
        return num * 365 * 86400

    return 0
