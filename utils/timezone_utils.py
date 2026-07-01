from datetime import datetime
from zoneinfo import ZoneInfo

PH_TZ = ZoneInfo("Asia/Manila")


def now_ph_aware() -> datetime:
    """Return current timezone-aware datetime in Asia/Manila."""
    return datetime.now(PH_TZ)


def now_ph_naive() -> datetime:
    """
    Return current PH time as naive datetime.

    Useful for DB columns configured as timezone-naive DateTime,
    while still storing PH wall-clock time consistently.
    """
    return now_ph_aware().replace(tzinfo=None)


def format_ph(value, fmt: str = "%B %d, %Y %I:%M %p") -> str:
    """
    Format datetime in PH timezone safely.

    - If value is naive, it is treated as PH wall-clock time.
    - If value is aware, it is converted to PH timezone.
    """
    if value is None:
        return ""

    if value.tzinfo is None:
        dt = value
    else:
        dt = value.astimezone(PH_TZ)

    return dt.strftime(fmt)
